from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import CustomerData
from app.models.model import predict_churn

app = FastAPI()

# Enable CORS to allow Vue.js to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Churn Prediction API"}

@app.post("/predict")
async def predict(data: CustomerData):
    result = predict_churn(data)
    return result