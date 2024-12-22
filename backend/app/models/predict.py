import pickle
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load the model
with open("nnet.pkcls", "rb") as file:
    model = pickle.load(file)

# Define the API app
app = FastAPI()

# Define input schema for prediction
class Customer(BaseModel):
    age: int
    gender: str
    tenure: int
    usage_frequency: float
    support_calls: int
    payment_delay: int
    subscription_type: str
    contract_length: str
    total_spend: float
    last_interaction: int

# Define prediction endpoint
@app.post("/predict")
def predict(customer: Customer):
    try:
        # Preprocess input data (e.g., encode categorical variables)
        input_data = [
            customer.age,
            1 if customer.gender.lower() == "male" else 0,  # Example encoding for gender
            customer.tenure,
            customer.usage_frequency,
            customer.support_calls,
            customer.payment_delay,
            customer.total_spend,
            customer.last_interaction,
        ]
        
        # Make a prediction
        prediction = model.predict([input_data])
        probability = model.predict_proba([input_data])

        return {"churn": bool(prediction[0]), "probability": probability[0].tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
