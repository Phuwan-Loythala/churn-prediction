import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# Load your dataset
data = pd.read_csv("customer_churn_master.csv")

# Preprocessing: Convert categorical columns to numeric
label_encoder_geo = LabelEncoder()
label_encoder_gender = LabelEncoder()
label_encoder_subscription = LabelEncoder()
label_encoder_contract = LabelEncoder()

data["Geography"] = label_encoder_geo.fit_transform(data["Geography"])
data["Gender"] = label_encoder_gender.fit_transform(data["Gender"])
data["Subscription Type"] = label_encoder_subscription.fit_transform(data["Subscription Type"])
data["Contract Length"] = label_encoder_contract.fit_transform(data["Contract Length"])

# Check if target column exists
if "Churn" not in data.columns:
    raise ValueError("Target column 'Churn' is missing from the dataset.")

# Features and target
X = data[
    [
        "CustomerId",
        "Age",
        "Gender",
        "Tenure",
        "Usage_Frequency",
        "Support_Calls",
        "Payment_Delay",
        "Subscription_Type",
        "Contract_Length",
        "Total_Spend",
        "Last_Interaction",
    ]
]
y = data["Churn"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Save the model
joblib.dump(model, "gradient_boosting.pkcls")

print("Model training complete and saved as gradient_boosting.pkcls")
