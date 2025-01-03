import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# ใช้ Service Account Key ในการเชื่อมต่อ
def authenticate_google_sheets():
    # กำหนด scope สำหรับการเข้าถึง Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('app/service_account.json', scope)
    client = gspread.authorize(creds)
    return client

# ฟังก์ชันเก็บข้อมูลการทำนายใน Google Sheets
def log_prediction_to_sheet(customer_data, prediction, confidence):
    # เข้าถึง Google Sheets ด้วย gspread
    client = authenticate_google_sheets()
    sheet = client.open_by_key('1PMKShDQb9HQ1l0KbMjUPUxeSWN08BKP2xjqoMyPw5xE').sheet1  # เปิด Google Sheet ที่มีชื่อว่า 'Customer_Churn_Log'

    # ข้อมูลที่ต้องการบันทึก
    log_data = {
        "Age": customer_data['Age'],
        "Gender": customer_data['Gender'],
        "Tenure": customer_data['Tenure'],
        "Usage_Frequency": customer_data['Usage_Frequency'],
        "Support_Calls": customer_data['Support_Calls'],
        "Payment_Delay": customer_data['Payment_Delay'],
        "Subscription_Type": customer_data['Subscription_Type'],
        "Contract_Length": customer_data['Contract_Length'],
        "Total_Spend": customer_data['Total_Spend'],
        "Last_Interaction": customer_data['Last_Interaction'],
        "Prediction": "Churn" if prediction == 1 else "Not Churn",
        "Confidence": confidence,
        "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # เพิ่มข้อมูลลงในแถวใหม่ของ Google Sheets
    sheet.append_row(list(log_data.values()))

# ตัวอย่างการใช้ฟังก์ชัน log_prediction_to_sheet
if __name__ == "__main__":
    customer_data = {
        'Customer_ID': 123,
        'Age': 30,
        'Gender': 'Male',
        'Tenure': 12,
        'Usage_Frequency': 10,
        'Support_Calls': 5,
        'Payment_Delay': 3,
        'Subscription_Type': 'Premium',
        'Contract_Length': 'Annual',
        'Total_Spend': 1000.0,
        'Last_Interaction': 15
    }
    prediction = 1  # Churn
    confidence = 0.85

    log_prediction_to_sheet(customer_data, prediction, confidence)
