
import joblib
import pandas as pd

model = joblib.load("../models/rf_ahp_model.pkl")

new_laptop = pd.DataFrame([{
    "Norm_CPU": 0.8,
    "Norm_RAM": 0.9,
    "Norm_GPU": 0.5,
    "Norm_Screen": 0.7,
    "Norm_Weight": 0.6,
    "Norm_Battery": 0.8,
    "Norm_Durability": 0.7,
    "Norm_Upgrade": 0.6,
    "Price (VND)": 15000000
}])

score = model.predict(new_laptop)

print("Predicted AHP Score:", score[0])
