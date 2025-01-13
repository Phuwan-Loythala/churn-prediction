import streamlit as st
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from datetime import datetime
import toml
import pytz

# Load the .toml file
config = toml.load('app/config/config.toml')
# Set up logging configuration
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Access the configuration values
API_KEY = config['secrets']['API_KEY']
GOOGLE_CREDENTIALS_PATH = config['secrets']['GOOGLE_CREDENTIALS_PATH']
SHEET_ID = config['secrets']['SHEET_ID']
URL = config['secrets']['URL']

# Headers for Typhoon API requests
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def log_prediction_to_sheet(input_data, prediction, confidence):
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

        # Get the current time in Bangkok timezone
        local_time = datetime.now(bangkok_tz)

        # Format the timestamp
        timestamp = local_time.strftime('%Y-%m-%d %H:%M:%S')        

        # Log data to the sheet with correct column order
        # Modify the confidence format to ensure it's displayed correctly
        row = [
            input_data.get("Age"),
            input_data.get("Gender"),
            input_data.get("Tenure"),
            input_data.get("Usage_Frequency"),
            input_data.get("Support_Calls"),
            input_data.get("Payment_Delay"),
            input_data.get("Subscription_Type"),
            input_data.get("Contract_Length"),
            input_data.get("Total_Spend"),
            input_data.get("Last_Interaction"),
            "Churn" if prediction == 1 else "Not Churn",
            confidence,
            timestamp
        ]
        sheet.append_row(row)
        st.success("Data logged successfully!")
        logging.info(f"Logged prediction for customer: {input_data['Age']}, Prediction: {'Churn' if prediction == 1 else 'Not Churn'}")
    except gspread.exceptions.APIError as e:
        logging.error(f"Google Sheets API error: {e}")
        st.error(f"Google Sheets API error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in logging to Google Sheets: {e}")
        st.error(f"Unexpected error: {e}")

def query_typhoon_api(prompt):
    """Query Typhoon Thai GPT API for explanations."""
    try:
        payload = {
            "model": "typhoon-v1.5x-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "temperature": 0.7,
        }
        response = requests.post(URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise error for non-200 responses
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

def fit_label_encoder_on_data(data):
    """Encode categorical data."""
    label_encoders = {
        "Gender": LabelEncoder(),
        "Subscription_Type": LabelEncoder(),
        "Contract_Length": LabelEncoder(),
    }
    for col, encoder in label_encoders.items():
        data[col] = encoder.fit_transform(data[col])
    return label_encoders

def safe_transform(encoder, value):
    """Safely transform input values."""
    try:
        return encoder.transform([value])[0]
    except ValueError:
        return encoder.transform([encoder.classes_[0]])[0]

def predict_churn_single(input_data, label_encoders, model, X):
    """Make predictions for a single customer."""
    try:
        input_df = pd.DataFrame([input_data])
        for col, encoder in label_encoders.items():
            input_df[col] = safe_transform(encoder, input_df[col].iloc[0])
        input_df = input_df[X.columns]
        prediction = model.predict(input_df)[0]
        confidence = max(model.predict_proba(input_df)[0])
        logging.info(f"Prediction made for input data: {input_data}, Prediction: {'Churn' if prediction == 1 else 'Not Churn'}, Confidence: {confidence * 100:.2f}%")
        return prediction, confidence
    except Exception as e:
        logging.error(f"Error in prediction: {e}")
        st.error(f"Error in prediction: {e}")
        return None, None

def explain_prediction_with_typhoon(prediction, confidence, input_data):
    """Generate an explanation for the prediction using Typhoon Thai GPT."""
    details = (
        f"อายุ: {input_data['Age']} ปี, เพศ: {input_data['Gender']}, "
        f"ระยะเวลาใช้งาน: {input_data['Tenure']} เดือน, "
        f"ความถี่การใช้งาน: {input_data['Usage_Frequency']} ครั้ง/เดือน, "
        f"จำนวนครั้งที่ติดต่อฝ่ายสนับสนุน: {input_data['Support_Calls']} ครั้ง, "
        f"การชำระเงินล่าช้า: {input_data['Payment_Delay']} วัน, "
        f"ประเภทสมาชิก: {input_data['Subscription_Type']}, "
        f"ระยะเวลาสัญญา: {input_data['Contract_Length']}, "
        f"ยอดใช้จ่ายรวม: {input_data['Total_Spend']} บาท, "
        f"วันที่ใช้งานล่าสุด: {input_data['Last_Interaction']} วันที่ผ่านมา"
    )
    explanation_prompt = (
        f"โมเดลพยากรณ์ผลลัพธ์เป็น {'Churn' if prediction == 1 else 'Not Churn'} "
        f"โดยมีระดับความมั่นใจ {confidence * 100:.2f}%. "
        f"ข้อมูลของลูกค้ามีดังนี้: {details}. "
        f"กรุณาอธิบายเหตุผลและให้คำแนะนำสำหรับลูกค้ารายนี้เป็นภาษาไทย"
    )
    return query_typhoon_api(explanation_prompt)


# Load data and train model
try:
    data = pd.read_csv('app/customer_churn_master.csv')
    label_encoders = fit_label_encoder_on_data(data)
    X = data.drop('Churn', axis=1)
    y = data['Churn']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    joblib.dump(model, 'model/randomforest.pkcls')
except Exception as e:
    st.error(f"Error loading data or model: {e}")
    st.stop()

# Streamlit settings
st.set_page_config(page_title="พยากรณ์การสูญเสียลูกค้า", layout="centered")
st.title("พยากรณ์การสูญเสียลูกค้า")

# UI options
option = st.radio("เลือกวิธีการทำนาย:", ["ฟอร์มทำนายลูกค้าเดียว", "อัปโหลดไฟล์ CSV"])

if option == "ฟอร์มทำนายลูกค้าเดียว":
    st.subheader("ทำนายการสูญเสียลูกค้าจากฟอร์ม")
    with st.form("churn_form"):
        # Form inputs
        input_data = {
            "Age": st.number_input("อายุ", 0, 120, step=1),
            "Gender": st.selectbox("เพศ", ["Male", "Female"]),
            "Tenure": st.number_input("ระยะเวลาใช้งาน (เดือน)", 0, step=1),
            "Usage_Frequency": st.number_input("ความถี่การใช้งาน (ครั้ง/เดือน)", 0, step=1),
            "Support_Calls": st.number_input("จำนวนครั้งที่ติดต่อฝ่ายสนับสนุน", 0, step=1),
            "Payment_Delay": st.number_input("การชำระเงินล่าช้า (วัน)", 0, step=1),
            "Subscription_Type": st.selectbox("ประเภทสมาชิก", ["Basic", "Standard", "Premium"]),
            "Contract_Length": st.selectbox("ระยะเวลาสัญญา", ["Monthly", "Quarterly", "Yearly"]),
            "Total_Spend": st.number_input("ยอดใช้จ่ายรวม (บาท)", 0.0, step=100.0),
            "Last_Interaction": st.number_input("วันที่ใช้งานล่าสุด (วัน)", 0, step=1),
        }
        submitted = st.form_submit_button("เริ่มการทำนาย")
        
        if submitted:
            prediction, confidence = predict_churn_single(input_data, label_encoders, model, X)
            if prediction is not None:
                explain_text = explain_prediction_with_typhoon(prediction, confidence, input_data)
                st.write(explain_text)
                log_prediction_to_sheet(input_data, prediction, confidence)

# Handle CSV upload for multiple predictions
if option == "อัปโหลดไฟล์ CSV":
    uploaded_file = st.file_uploader("เลือกไฟล์ CSV", type="csv")
    if uploaded_file is not None:
        # Read CSV file
        try:
            input_data_csv = pd.read_csv(uploaded_file)
            st.write(input_data_csv)

            # Preprocess and predict for each row in the CSV
            for index, row in input_data_csv.iterrows():
                prediction, confidence = predict_churn_single(row.to_dict(), label_encoders, model, X)
                if prediction is not None:
                    explain_text = explain_prediction_with_typhoon(prediction, confidence, row.to_dict())
                    st.write(explain_text)
                    log_prediction_to_sheet(row.to_dict(), prediction, confidence)
        except Exception as e:
            st.error(f"Error processing CSV file: {e}")
