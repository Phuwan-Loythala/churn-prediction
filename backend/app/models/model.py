from fastapi import FastAPI  # Import FastAPI
import os
import joblib
from pydantic import BaseModel
from app.models.schemas import CustomerData


# Create an instance of FastAPI
app = FastAPI()

# Get the absolute path to the model file
model_path = os.path.join(os.path.dirname(__file__), 'lgbm_churn_model.pkl')

# Load the pre-trained ML model
model = joblib.load(model_path)

def predict_churn(data: CustomerData):
    # Prepare input for the model
    features = [[
        data.credit_score,
        data.geography,
        data.gender,
        data.age,
        data.tenure,
        data.balance,
        data.num_of_products,
        data.has_credit_card,
        data.is_active_member,
        data.estimated_salary
    ]]
    # Make prediction
    prediction = model.predict(features)
    return {"churn": bool(prediction[0])}

# Define the input schema for the customer data
class Customer(BaseModel):
    credit_score: int
    geography: int
    gender: int
    age: int
    tenure: int
    balance: float
    num_of_products: int
    has_credit_card: int
    is_active_member: int
    estimated_salary: float

# Define the route for prediction
@app.post("/predict")
async def predict_churn(customer: Customer):
    # Prepare the customer input data into a format suitable for prediction
    features = [[
        customer.credit_score,
        customer.geography,
        customer.gender,
        customer.age,
        customer.tenure,
        customer.balance,
        customer.num_of_products,
        customer.has_credit_card,
        customer.is_active_member,
        customer.estimated_salary
    ]]

    # Use the model to predict churn (assuming binary classification)
    prediction = model.predict(features)[0]  # 0 for no churn, 1 for churn

    # Get the probability for the predicted class
    probability = model.predict_proba(features)[0][prediction]  # Probability of the predicted class

    # Return the prediction result
    return {"churn": prediction, "probability": probability}