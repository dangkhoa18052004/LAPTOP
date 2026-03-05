
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import numpy as np

# Load dataset
df = pd.read_excel("../data/AHP_Laptop_Nhom8.xlsx", sheet_name="Laptop_Data")

features = [
    "Norm_CPU", "Norm_RAM", "Norm_GPU",
    "Norm_Screen", "Norm_Weight",
    "Norm_Battery", "Norm_Durability",
    "Norm_Upgrade", "Price (VND)"
]

target = "AHP Score"

df = df.dropna(subset=features + [target])

X = df[features]
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("===== MODEL EVALUATION =====")
print("R2:", r2_score(y_test, y_pred))
print("MAE:", mean_absolute_error(y_test, y_pred))
print("RMSE:", np.sqrt(mean_squared_error(y_test, y_pred)))

# Save model
joblib.dump(model, "../models/rf_ahp_model.pkl")

print("Model saved to models/rf_ahp_model.pkl")
