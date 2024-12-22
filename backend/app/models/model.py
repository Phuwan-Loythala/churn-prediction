import os
import joblib
from app.models.schemas import CustomerData

# Get the absolute path to the model file
model_path = os.path.join(os.path.dirname(__file__), 'nnet.pkcls')

# Load the pre-trained ML model
model = joblib.load(model_path)

def predict_churn(data: CustomerData):
    # Prepare input for the model
    features = [
        data.CustomerID,
        data.Age,
        data.Gender,
        data.Tenure,
        data.Usage_Frequency,
        data.Support_Calls,
        data.Payment_Delay,
        data.Subscription_Type,
        data.Contract_Length,
        data.Total_Spend,
        data.Last_Interaction,
        data.Churn,
    ]
    # Make prediction
    prediction = model.predict(features)
    return {"churn": bool(prediction[0])}
