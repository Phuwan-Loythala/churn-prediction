import streamlit as st
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import openai
import time
from log_to_sheets import log_prediction_to_sheet

# OpenAI API Key
OPENAI_API_KEY = "sk-your-api-key"  # ใส่ API Key ของคุณที่นี่

# ฟังก์ชันส่งคำขอไปยัง OpenAI ChatGPT API
def query_chatgpt_api(prompt, api_key):
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful assistant that provides explanations in Thai."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ข้อผิดพลาด: {e}"

# ฟังก์ชันเข้ารหัสข้อมูล
def fit_label_encoder_on_data(data):
    label_encoder_gender = LabelEncoder()
    label_encoder_subscription = LabelEncoder()
    label_encoder_contract = LabelEncoder()

    data['Gender'] = label_encoder_gender.fit_transform(data['Gender'])
    data['Subscription_Type'] = label_encoder_subscription.fit_transform(data['Subscription_Type'])
    data['Contract_Length'] = label_encoder_contract.fit_transform(data['Contract_Length'])

    return label_encoder_gender, label_encoder_subscription, label_encoder_contract

# ฟังก์ชันแปลงข้อมูลที่ไม่เคยเห็นจาก LabelEncoder
def safe_transform(encoder, value):
    try:
        return encoder.transform([value])[0]
    except ValueError:
        # ค่าที่ไม่เคยเห็นจะถูกแปลงเป็นค่า default (เช่น 0)
        return encoder.transform([encoder.classes_[0]])[0]

# ฟังก์ชันทำนาย
def predict_churn_single(input_data, label_encoders, model, X):
    label_encoder_gender, label_encoder_subscription, label_encoder_contract = label_encoders
    input_df = pd.DataFrame([input_data])

    # ใช้ safe_transform ในการแปลงค่า
    input_df['Gender'] = safe_transform(label_encoder_gender, input_df['Gender'])
    input_df['Subscription_Type'] = safe_transform(label_encoder_subscription, input_df['Subscription_Type'])
    input_df['Contract_Length'] = safe_transform(label_encoder_contract, input_df['Contract_Length'])

    input_df = input_df[X.columns]
    prediction = model.predict(input_df)[0]
    confidence = max(model.predict_proba(input_df)[0])

    return prediction, confidence

# ฟังก์ชันอธิบายผลลัพธ์
def explain_prediction_with_chatgpt(prediction, confidence, input_data):
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

    explanation = query_chatgpt_api(explanation_prompt, OPENAI_API_KEY)
    return explanation

# โหลดข้อมูลและโมเดล
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

st.set_page_config(page_title="พยากรณ์การสูญเสียลูกค้า", layout="centered")
st.title("พยากรณ์การสูญเสียลูกค้า")

# เพิ่มตัวเลือกสำหรับการเลือกวิธีการทำนาย
option = st.radio("เลือกวิธีการทำนาย:", ["ฟอร์มทำนายลูกค้าเดียว", "อัปโหลดไฟล์ CSV"])

# ฟังก์ชันทำนายแบบฟอร์ม
if option == "ฟอร์มทำนายลูกค้าเดียว":
    st.subheader("ทำนายการสูญเสียลูกค้าจากฟอร์ม")
    with st.form("churn_form"):
        # ... (ส่วนของโค้ดในฟอร์ม)

        submitted = st.form_submit_button("เริ่มการทำนาย")

    if submitted:
        with st.spinner("กำลังประมวลผล..."):
            progress_bar = st.progress(0)
            for percent_complete in range(0, 101, 10):
                progress_bar.progress(percent_complete / 100)
                time.sleep(0.1)

            input_data = {
                "Age": age,
                "Gender": gender,
                "Tenure": tenure,
                "Usage_Frequency": usage_frequency,
                "Support_Calls": support_calls,
                "Payment_Delay": payment_delay,
                "Subscription_Type": subscription_type,
                "Contract_Length": contract_length,
                "Total_Spend": total_spend,
                "Last_Interaction": last_interaction
            }

            prediction, confidence = predict_churn_single(input_data, label_encoders, model, X)

            if prediction == 1:
                st.error(f"The customer is likely to churn with a confidence of {confidence * 100:.2f}%.")
            else:
                st.success(f"The customer is unlikely to churn with a confidence of {confidence * 100:.2f}%.")
            
            explanation = explain_prediction_with_chatgpt(prediction, confidence, input_data)
            st.write("Explanation:")
            st.write(explanation)

            # เรียกฟังก์ชัน log เพื่อบันทึกผลการทำนายลง Google Sheets
            log_prediction_to_sheet(input_data, prediction, confidence)

# ฟังก์ชันทำนายจากไฟล์ CSV
elif option == "อัปโหลดไฟล์ CSV":
    st.subheader("ทำนายการสูญเสียลูกค้า (อัปโหลดไฟล์ CSV)")
    uploaded_file = st.file_uploader("อัปโหลดไฟล์ CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # ตรวจสอบคอลัมน์ที่มีอยู่ในข้อมูล
        required_columns = ['Age', 'Gender', 'Tenure', 'Usage_Frequency', 'Support_Calls', 
                            'Payment_Delay', 'Subscription_Type', 'Contract_Length', 'Total_Spend', 'Last_Interaction']
        if not all(col in df.columns for col in required_columns):
            st.error("ไฟล์ CSV ไม่ครบถ้วนตามที่ต้องการ กรุณาตรวจสอบคอลัมน์")
        else:
            # ทำนายผลลัพธ์
            label_encoders = fit_label_encoder_on_data(df)
            X_input = df[required_columns]

            # ทำนายทุกแถวในข้อมูล
            predictions = []
            confidences = []

            for _, row in X_input.iterrows():
                input_data = row.to_dict()
                prediction, confidence = predict_churn_single(input_data, label_encoders, model, X)
                predictions.append(prediction)
                confidences.append(confidence)

            # เพิ่มผลลัพธ์ทำนายเข้าไปใน DataFrame
            df['Churn Prediction'] = ['Churn' if pred == 1 else 'Not Churn' for pred in predictions]
            df['Confidence %'] = [conf * 100 for conf in confidences]

            # แสดงผลลัพธ์
            st.write("ผลลัพธ์การทำนายการสูญเสียลูกค้า:")
            st.dataframe(df)

            # ดาวน์โหลดผลลัพธ์เป็นไฟล์ CSV
            csv_output = df.to_csv(index=False)
            st.download_button(
                label="ดาวน์โหลดผลลัพธ์เป็นไฟล์ CSV",
                data=csv_output,
                file_name="customer_churn_predictions.csv",
                mime="text/csv"
            )
