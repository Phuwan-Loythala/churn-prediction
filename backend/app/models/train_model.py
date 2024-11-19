import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# Load your dataset
data = pd.read_csv("churn_data.csv")

# Preprocessing: Convert categorical columns to numeric
label_encoder = LabelEncoder()
data["Geography"] = label_encoder.fit_transform(data["Geography"])
data["Gender"] = label_encoder.fit_transform(data["Gender"])

# Features and target
X = data[
    [
        "CreditScore",
        "Geography",
        "Gender",
        "Age",
        "Tenure",
        "Balance",
        "NumOfProducts",
        "HasCrCard",
        "IsActiveMember",
        "EstimatedSalary",
    ]
]
y = data["Exited"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Save the model
joblib.dump(model, "model/churn_model.pkl")

print("Model training complete and saved as churn_model.pkl")
