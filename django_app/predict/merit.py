import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from dataclasses import dataclass

# --- Random Forest Setup ---
# We train on the "Gap" (Merit - Cutoff) to predict Probability %
# Based on your data: +2 diff = 73.5% chance, 0 diff = 60%, etc.
X_train = np.array([[-10], [-5], [-2], [0], [2], [5], [10]]).reshape(-1, 1)
y_train = np.array([10.0, 26.25, 42.0, 60.0, 73.5, 94.5, 98.0])

rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

@dataclass
class MeritResult:
    final_merit: float
    theory_percent: float
    gujcet_percent: float

def calculate_merit(theory_ob, theory_tot, gujcet, has_farming):
    # 60% Theory + 40% GUJCET
    theory_p = (theory_ob / theory_tot) * 60
    gujcet_p = (gujcet / 120) * 40
    merit = theory_p + gujcet_p
    
    if has_farming:
        merit += 5.0 # Fixed 5% bonus points
        
    return MeritResult(
        final_merit=round(min(merit, 100), 4),
        theory_percent=round(theory_p, 4),
        gujcet_percent=round(gujcet_p, 4)
    )

def get_rf_prediction(merit, cutoff):
    if not cutoff or cutoff == 0:
        return {"chance": 0, "label": "Wait Recommended"}
    
    diff = merit - cutoff
    prob = rf_model.predict([[diff]])[0]
    
    label = "High" if prob >= 85 else "Medium" if prob >= 50 else "Low"
    return {"chance": round(prob, 2), "label": label}