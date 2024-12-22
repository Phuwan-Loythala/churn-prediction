from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib  # For loading the model

# Define the schema for customer data
class CustomerData(BaseModel):
    CustomerID: int
    Age: int
    Gender: str  # Male, Female
    Tenure: int
    Usage_Frequency: int
    Support_Calls: int
    Payment_Delay: int
    Subscription_Type: str  # Basic, Standard, Premium
    Contract_Length: str  # Monthly, Quarterly, Annual
    Total_Spend: float
    Last_Interaction: int

# Load your trained model (ensure you have a pre-trained model saved as 'model.pkl')
model = joblib.load("/workspaces/codespaces-blank/churn-prediction/backend/app/models/nnet.pkcls")

app = FastAPI()

# Enable CORS to allow Vue.js to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://super-duper-space-robot-579w4pjvwww345p5-5173.app.github.dev"],  # Remove trailing '/'
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Churn Prediction API"}

@app.post("/predict")
async def predict_churn(data: CustomerData):
    # Prepare the input data for prediction (convert categorical variables if needed)
    input_data = [
        data.Age,
        data.Gender,  # Encoding for gender (0: Male, 1: Female)
        data.Tenure,
        data.Usage_Frequency,
        data.Support_Calls,
        data.Payment_Delay,
        data.Subscription_Type,  # Encoding for subscription type (Basic: 0, Standard: 1, Premium: 2)
        data.Contract_Length,  # Encoding for contract length (Monthly: 0, Quarterly: 1, Annual: 2)
        data.Total_Spend,
        data.Last_Interaction,
    ]

    # Encode Gender (Male: 0, Female: 1)
    if data.Gender == "Male":
        input_data[1] = 0
    elif data.Gender == "Female":
        input_data[1] = 1

    # Encode Subscription Type (Basic: 0, Standard: 1, Premium: 2)
    if data.Subscription_Type == "Basic":
        input_data[6] = 0
    elif data.Subscription_Type == "Standard":
        input_data[6] = 1
    else:
        input_data[6] = 2

    # Encode Contract Length (Monthly: 0, Quarterly: 1, Annual: 2)
    if data.Contract_Length == "Monthly":
        input_data[7] = 0
    elif data.Contract_Length == "Quarterly":
        input_data[7] = 1
    else:
        input_data[7] = 2

    # Predict churn using the trained model
    prediction = model.predict([input_data])  # Make prediction using the model

    # Return prediction (convert numeric output to boolean)
    churn = True if prediction[0] == 1 else False
    return {"churn": churn}
