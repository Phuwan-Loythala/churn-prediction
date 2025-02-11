import streamlit as st
import pandas as pd
import joblib
import logging
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import requests
import toml
import os

# Load the .toml file
config = toml.load('app/config/config.toml')

# Access the configuration values
API_KEY = config['secrets']['API_KEY']
GOOGLE_CREDENTIALS_PATH = config['secrets']['GOOGLE_CREDENTIALS_PATH']
SHEET_ID = config['secrets']['SHEET_ID']
URL = config['secrets']['URL']

# Streamlit page configuration
st.set_page_config(page_title="Customer Churn Prediction", layout="centered")

@st.cache_data
def load_data():
    data = pd.read_csv('model/customer_churn_dataset_updated.csv')
    data["Contract_Length=Monthly"] = data["Contract_Length=Monthly"].apply(lambda x: 1 if x == "Monthly" else 0)
    return data

# Load dataset and split into training/testing
raw_data = load_data()
X = raw_data.drop('Churn', axis=1)
y = raw_data['Churn']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

@st.cache_resource
def load_model():
    try:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        joblib.dump(model, "model/random_forest.pkcls")
        return model
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        return None

model = load_model()

def log_prediction_to_sheet(input_data, prediction, confidence, recommendation):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_PATH, scope)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(SHEET_ID).sheet1
        bangkok_tz = pytz.timezone('Asia/Bangkok')
        timestamp = datetime.now(bangkok_tz).strftime('%Y-%m-%d %H:%M:%S')
        row = [
            input_data.get("Support_Calls"), input_data.get("Total_Spend"),
            input_data.get("Payment_Delay"), "Monthly" if input_data.get("Contract_Length=Monthly") else "Other",
            "Churn" if prediction == 1 else "Not Churn", confidence, recommendation, timestamp
        ]
        sheet.append_row(row)
        logging.info(f"Logged prediction: {row}")
    except Exception as e:
        logging.error(f"Error logging to Google Sheets: {e}")

def query_typhoon_api(prompt, language="th"):
    try:
        payload = {
            "model": "typhoon-v1.5x-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500, "temperature": 0.7,
        }
        response = requests.post(URL, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        logging.error(f"API HTTPError: {e}")
        return "API Error"
    except Exception as e:
        logging.error(f"API Error: {e}")
        return "Unexpected Error"

def process_csv_predictions(input_data_csv):
    expected_columns = X.columns.tolist()
    input_data_csv = input_data_csv.rename(columns={"Contract_Length_Monthly": "Contract_Length=Monthly"})
    for col in expected_columns:
        if col not in input_data_csv.columns:
            input_data_csv[col] = 0
    input_data_csv["Contract_Length=Monthly"] = input_data_csv["Contract_Length=Monthly"].apply(lambda x: 1 if x == "Monthly" else 0)
    predictions = model.predict(input_data_csv[expected_columns])
    confidences = model.predict_proba(input_data_csv[expected_columns])
    results = []
    for i, prediction in enumerate(predictions):
        confidence = max(confidences[i])
        prompt = f"Given the following data: {input_data_csv.iloc[i].to_dict()}, what is the recommendation?"
        recommendation = query_typhoon_api(prompt)
        results.append((prediction, confidence, recommendation))
    return results

def predict_churn_single(input_data):
    input_df = pd.DataFrame([input_data])[X.columns]
    if model is None:
        return None, None, "Model not available"
    try:
        prediction = model.predict(input_df)[0]
        confidence = model.predict_proba(input_df)[0][prediction]
        prompt = f"ให้ข้อมูลดังต่อไปนี้: {input_data}, คุณจะแนะนำอย่างไรในภาษาไทย ถ้าคุณเป็นนักวิเคราะห์ข้อมูลของระบบพยากรณ์การสูญเสียลูกค้า?"
        recommendation = query_typhoon_api(prompt)
        return prediction, confidence, recommendation
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return None, None, "Error occurred"

st.title("Customer Churn Prediction")
option = st.radio("Select a prediction method:", ["Single Customer Form", "Upload CSV File"])

if option == "Single Customer Form":
    with st.form("churn_form"):
        input_data = {
            "Support_Calls": st.number_input("Number of Support Calls", 0, step=1),
            "Total_Spend": st.number_input("Total Spend (USD)", 0.0, step=0.01),
            "Payment_Delay": st.number_input("Payment Delay (days)", 0, step=1),
            "Contract_Length=Monthly": st.checkbox("Monthly Contract")
        }
        submitted = st.form_submit_button("Predict")
        if submitted:
            prediction, confidence, recommendation = predict_churn_single(input_data)
            if prediction is not None:
                st.write(f"Prediction: {'Churn' if prediction == 1 else 'Not Churn'}")
                st.write(f"Confidence: {confidence * 100:.2f}%")
                st.write(f"Recommendation: {recommendation}")
                log_prediction_to_sheet(input_data, prediction, confidence, recommendation)

if option == "Upload CSV File":
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    if uploaded_file is not None:
        input_data_csv = pd.read_csv(uploaded_file)
        results = process_csv_predictions(input_data_csv)
        for i, (prediction, confidence, recommendation) in enumerate(results):
            st.write(f"Row {i + 1}: {'Churn' if prediction == 1 else 'Not Churn'} ({confidence * 100:.2f}% confidence)")
            st.write(f"Recommendation: {recommendation}")