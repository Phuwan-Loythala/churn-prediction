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

# Load the .toml file
config = toml.load('app/config/config.toml')

# Access the configuration values
API_KEY = config['secrets']['API_KEY']
GOOGLE_CREDENTIALS_PATH = config['secrets']['GOOGLE_CREDENTIALS_PATH']
SHEET_ID = config['secrets']['SHEET_ID']
URL = config['secrets']['URL']

# Streamlit page configuration (MUST BE FIRST Streamlit command)
st.set_page_config(page_title="Customer Churn Prediction", layout="centered")

# Cache dataset loading
@st.cache_data
def load_data():
    data = pd.read_csv('model/customer_churn_dataset_updated.csv')
    data = data[["Support_Calls", "Total_Spend", "Payment_Delay", "Contract_Length=Monthly", "Churn"]]
    data["Contract_Length=Monthly"] = data["Contract_Length=Monthly"].apply(lambda x: 1 if x == "Monthly" else 0)
    return data

# Cache model loading
@st.cache_resource
def load_model():
    return joblib.load('model/random_forest.pkcls')

# Google Sheets Logging Function
def log_prediction_to_sheet(input_data, prediction, confidence, recommendation):
    try:
        # Define the scope
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Load credentials from JSON key file
        credentials = ServiceAccountCredentials.from_json_keyfile_name("app/config/servacc.json", scope)
        client = gspread.authorize(credentials)
        # Open the Google Sheet
        sheet = client.open_by_key("1PMKShDQb9HQ1l0KbMjUPUxeSWN08BKP2xjqoMyPw5xE").sheet1
        # Define Bangkok timezone
        bangkok_tz = pytz.timezone('Asia/Bangkok')
        timestamp = datetime.now(bangkok_tz).strftime('%Y-%m-%d %H:%M:%S')
        # Log data to the sheet
        row = [
            input_data.get("Support_Calls"),
            input_data.get("Total_Spend"),
            input_data.get("Payment_Delay"),
            "Monthly" if input_data.get("Contract_Length=Monthly") else "Other",
            "Churn" if prediction == 1 else "Not Churn",
            confidence,
            recommendation,
            timestamp
        ]
        sheet.append_row(row)
        logging.info(f"Logged prediction: {row}")
    except Exception as e:
        logging.error(f"Error logging to Google Sheets: {e}")

# Headers for Typhoon API requests
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def query_typhoon_api(prompt, language="th"):
    """
    Query Typhoon Thai GPT API เพื่อขอคำอธิบาย (ภาษาไทยตามค่าเริ่มต้น)
    :param prompt: ข้อความคำถามหรือคำขอที่ต้องการส่งให้ API
    :param language: ภาษาในการตอบกลับ ("th" สำหรับภาษาไทย)
    :return: ข้อความคำตอบจาก API
    """
    try:
        # ตรวจสอบการตั้งค่าภาษา
        if language == "th":
            prompt = f"ข้อมูลดังนี้: {prompt} กรุณาอธิบายเป็นภาษาไทย แต่ว่าใช้สกุลเงิน USD"
        
        # ข้อมูล payload
        payload = {
            "model": "typhoon-v1.5x-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "temperature": 0.7,
        }
        # ส่งคำขอไปยัง API
        response = requests.post(URL, headers=headers, json=payload)
        response.raise_for_status()  # หากเกิดข้อผิดพลาด HTTP จะ raise exception
        result = response.json()
        logging.info(f"Typhoon API response received successfully: {result}")
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        logging.error(f"API HTTPError: {e}")
        st.error(f"API HTTPError: {e}")
        return f"API HTTPError: {e}"
    except Exception as e:
        logging.error(f"Unexpected Error in API request: {e}")
        st.error(f"Unexpected Error: {e}")
        return f"Unexpected Error: {e}"
        
def process_csv_predictions(input_data_csv, model, X):
    results = []
    input_data_csv["Contract_Length=Monthly"] = input_data_csv["Contract_Length=Monthly"].apply(lambda x: 1 if x == "Monthly" else 0)
    predictions = model.predict(input_data_csv[X.columns])
    confidences = model.predict_proba(input_data_csv[X.columns])
    for i, prediction in enumerate(predictions):
        confidence = max(confidences[i])
        # Prepare prompt for Typhoon API
        row_data = {
            "Support_Calls": input_data_csv.iloc[i]["Support_Calls"],
            "Total_Spend": input_data_csv.iloc[i]["Total_Spend"],
            "Payment_Delay": input_data_csv.iloc[i]["Payment_Delay"],
            "Contract_Length": "Monthly" if input_data_csv.iloc[i]["Contract_Length=Monthly"] else "Other",
            "Prediction": "Churn" if prediction == 1 else "Not Churn"
        }
        prompt = f"Given the following data: {row_data}, what is the recommendation?"
        recommendation = query_typhoon_api(prompt)  # Use the old synchronous function
        results.append((prediction, confidence, recommendation))
    return results

# Prediction Function for Single Input
def predict_churn_single(input_data, model, X):
    input_df = pd.DataFrame([input_data])
    input_df = input_df[X.columns]
    prediction = model.predict(input_df)[0]
    confidence = max(model.predict_proba(input_df)[0])
    logging.info(f"Prediction: {prediction}, Confidence: {confidence * 100:.2f}%")
    
    # Prepare prompt for Typhoon API
    data = {
        "Support_Calls": input_data.get("Support_Calls"),
        "Total_Spend": input_data.get("Total_Spend"),
        "Payment_Delay": input_data.get("Payment_Delay"),
        "Contract_Length": "Monthly" if input_data.get("Contract_Length=Monthly") else "Other",
        "Prediction": "Churn" if prediction == 1 else "Not Churn"
    }
    prompt = f"Given the following data: {data}, what is the recommendation?"
    recommendation = query_typhoon_api(prompt)  # Use the old synchronous function
    return prediction, confidence, recommendation

# Load data and model
data = load_data()
X = data.drop('Churn', axis=1)
y = data['Churn']
model = load_model()

# Streamlit App UI
st.title("Customer Churn Prediction")
option = st.radio("Select a prediction method:", ["Single Customer Form", "Upload CSV File"])

if option == "Single Customer Form":
    st.subheader("Predict Churn for a Single Customer")
    with st.form("churn_form"):
        input_data = {
            "Support_Calls": st.number_input("Number of Support Calls", 0, step=1),
            "Total_Spend": st.number_input("Total Spend (USD)", 0.0, step=0.01),
            "Payment_Delay": st.number_input("Payment Delay (days)", 0, step=1),
            "Contract_Length=Monthly": st.checkbox("Monthly Contract")
        }
        input_data["Contract_Length=Monthly"] = 1 if input_data["Contract_Length=Monthly"] else 0
        submitted = st.form_submit_button("Predict")
        # In Streamlit Form: Call the updated predict_churn_single function to get the recommendation
        if submitted:
            prediction, confidence, recommendation = predict_churn_single(input_data, model, X)
            st.write(f"Prediction: {'Churn' if prediction == 1 else 'Not Churn'}")
            st.write(f"Confidence: {confidence * 100:.2f}%")
            st.write(f"Recommendation: {recommendation}")
            log_prediction_to_sheet(input_data, prediction, confidence, recommendation)

if option == "Upload CSV File":
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    if uploaded_file is not None:
        input_data_csv = pd.read_csv(uploaded_file)
        results = process_csv_predictions(input_data_csv, model, X)
        for i, (prediction, confidence, recommendation) in enumerate(results):
            st.write(f"Row {i + 1}: {'Churn' if prediction == 1 else 'Not Churn'} ({confidence * 100:.2f}% confidence)")
            st.write(f"Recommendation: {recommendation}")
