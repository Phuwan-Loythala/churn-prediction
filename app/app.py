import streamlit as st
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import requests
import os
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Set up Google Cloud credentials and API scopes
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "app/service_account.json"
credentials = service_account.Credentials.from_service_account_file(
    'app/service_account.json',
    scopes=["https://www.googleapis.com/auth/generative-language.retriever"]
)

# Refresh the credentials
credentials.refresh(Request())
access_token = credentials.token

# Headers for API requests
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}

# Log predictions to Google Sheets (Placeholder function)
def log_prediction_to_sheet(input_data, prediction, confidence):
    # Dummy implementation - replace with your actual logic
    st.write("Logged prediction to Google Sheets.")

# Replace with your Gemini API Key
GEMINI_API_KEY = "AIzaSyDPLCNH1fxkc-xYck4njQOz3WsCjWL_5q0"

# ... (rest of the code)

def query_gemini_api(prompt):
    """Query Gemini API for explanations."""
    try:
        headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            # ... (rest of the data)
        }
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta2/models/gemini-1.5-flash:generateText",
            json=data,
            headers=headers,
        )
        response.raise_for_status()  # Raise an exception for error HTTP statuses
        result = response.json()
        return result["candidates"][0]["output"] if "candidates" in result else "No response."
    except requests.exceptions.HTTPError as e:
        return f"Error querying Gemini API: {e}. Please check your API key and network connection."
    except Exception as e:
        return f"Unexpected error: {e}"

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
    input_df = pd.DataFrame([input_data])
    for col, encoder in label_encoders.items():
        input_df[col] = safe_transform(encoder, input_df[col].iloc[0])
    input_df = input_df[X.columns]
    prediction = model.predict(input_df)[0]
    confidence = max(model.predict_proba(input_df)[0])
    return prediction, confidence

def explain_prediction_with_gemini(prediction, confidence, input_data):
    """Generate an explanation for the prediction."""
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
    return query_gemini_api(explanation_prompt)

# Load data and train model
try:
    data = pd.read_csv('app/customer_churn_master.csv')
    label_encoders = fit_label_encoder_on_data(data)
    X = data.drop('Churn', axis=1)
    y = data['Churn']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    joblib.dump(model, 'randomproject1.pkcls')
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
            with st.spinner("กำลังประมวลผล..."):
                prediction, confidence = predict_churn_single(input_data, label_encoders, model, X)
                if prediction == 1:
                    st.error(f"ลูกค้ามีแนวโน้มจะเลิกใช้บริการ ({confidence * 100:.2f}%).")
                else:
                    st.success(f"ลูกค้าไม่น่าจะเลิกใช้บริการ ({confidence * 100:.2f}%).")
                explanation = explain_prediction_with_gemini(prediction, confidence, input_data)
                st.write("คำอธิบาย:")
                st.write(explanation)
                log_prediction_to_sheet(input_data, prediction, confidence)

elif option == "อัปโหลดไฟล์ CSV":
    st.subheader("ทำนายการสูญเสียลูกค้า (อัปโหลดไฟล์ CSV)")
    uploaded_file = st.file_uploader("อัปโหลดไฟล์ CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        required_columns = ["Age", "Gender", "Tenure", "Usage_Frequency", "Support_Calls",
                            "Payment_Delay", "Subscription_Type", "Contract_Length", "Total_Spend", "Last_Interaction"]
        if not all(col in df.columns for col in required_columns):
            st.error("ไฟล์ CSV ไม่ครบถ้วน กรุณาตรวจสอบคอลัมน์.")
        else:
            predictions, confidences = [], []
            for _, row in df.iterrows():
                input_data = row.to_dict()
                prediction, confidence = predict_churn_single(input_data, label_encoders, model, X)
                predictions.append("Churn" if prediction == 1 else "Not Churn")
                confidences.append(confidence * 100)
            df["Churn Prediction"] = predictions
            df["Confidence %"] = confidences
            st.dataframe(df)
            st.download_button(
                label="ดาวน์โหลดผลลัพธ์",
                data=df.to_csv(index=False),
                file_name="churn_predictions.csv",
                mime="text/csv"
            )
