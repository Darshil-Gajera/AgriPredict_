import pandas as pd
import numpy as np
import os
import traceback
from django.conf import settings
from sklearn.ensemble import RandomForestRegressor


class AgriPredictor:
    def __init__(self, category_id):
        self.category_id = str(category_id)
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self._train_model()

    def _train_model(self):
        train_data = [
            [-15.0, 5.25], [-10.0, 15.75], [-5.0, 26.25],
            [0.0, 60.0], [2.0, 73.5], [5.0, 94.5], [10.0, 98.0]
        ]
        X = np.array([i[0] for i in train_data]).reshape(-1, 1)
        y = np.array([i[1] for i in train_data])
        self.rf_model.fit(X, y)

    def calculate_merit(self, theory_ob, theory_tot, gujcet, has_farming):
        """Returns dict with keys: final_merit, theory_comp, gujcet_comp, bonus_comp"""
        if float(theory_tot) <= 0:
            raise ValueError("theory_total must be > 0")

        theory_component = (float(theory_ob) / float(theory_tot)) * 60.0
        gujcet_component = (float(gujcet) / 120.0) * 40.0
        merit = theory_component + gujcet_component
        bonus = 0.0

        if has_farming:
            merit += 5.0
            bonus = 5.0

        return {
            "final_merit": round(min(merit, 100.0), 4),
            "theory_comp": round(theory_component, 2),
            "gujcet_comp": round(gujcet_component, 2),
            "bonus_comp":  round(bonus, 2),          # always a float, never None
        }

    def get_recommendations(self, merit, student_cat):
        """
        Returns list of dicts with keys:
            name, course, location, cutoff, probability, chance_label, round_prediction

        CSV columns (actual, verified):
            SR NO. | COLLEGE NAME | COURSE | GENERAL | SEBC | SC | ST | EWS |
            Other Board | PH-VH | Ex - Serv. | Parsi

        After .strip().lower():
            sr no. | college name | course | general | sebc | sc | st | ews |
            other board | ph-vh | ex - serv. | parsi
        """

        # Maps form value → CSV column name after .strip().lower()
        CATEGORY_MAP = {
            "OPEN":    "general",
            "GENERAL": "general",
            "SEBC":    "sebc",
            "SC":      "sc",
            "ST":      "st",
            "EWS":     "ews",
            "OB":      "other board",
            "PH":      "ph-vh",
            "EX":      "ex - serv.",
        }

        target_col = CATEGORY_MAP.get(student_cat.strip().upper(), "general")

        file_path = os.path.join(
            settings.BASE_DIR,
            "predict", "data",
            f"category-{self.category_id}_collegewise_merit.csv",
        )

        print(f"\n📂 File: {file_path}")
        print(f"📂 Exists: {os.path.exists(file_path)}")
        print(f"🎯 Category: {student_cat!r} → column: {target_col!r}")

        if not os.path.exists(file_path):
            return self._error("CSV not found: " + file_path)

        try:
            df = pd.read_csv(file_path)

            # Normalize all column names
            df.columns = df.columns.str.strip().str.lower()
            print(f"📊 Columns: {list(df.columns)}")

            if target_col not in df.columns:
                # Try fuzzy match
                close = [c for c in df.columns if target_col.rstrip(".") in c]
                if close:
                    target_col = close[0]
                    print(f"⚠️ Fuzzy matched → {target_col!r}")
                else:
                    return self._error(f"Column '{target_col}' not found in CSV")

            # '-' and blanks → NaN
            df[target_col] = pd.to_numeric(df[target_col], errors="coerce")

            results = []
            for _, row in df.iterrows():
                cutoff = row[target_col]
                if pd.isna(cutoff) or float(cutoff) <= 0:
                    continue

                gap  = float(merit) - float(cutoff)
                prob = float(self.rf_model.predict([[gap]])[0])
                prob = max(0.0, min(100.0, prob))

                if prob >= 80:
                    label, chance = "High Chance",      "High"
                elif prob >= 40:
                    label, chance = "Medium Chance",    "Medium"
                else:
                    label, chance = "Wait Recommended", "Low"

                # Read college name — "college name" is the normalized CSV column
                college_name = self._cell(row, "college name", "college", "name")
                course_name  = self._cell(row, "course", "program", "branch")

                # Clean embedded newlines (seen in Cat-2 course names)
                college_name = college_name.replace("\n", " ").replace("\r", " ").strip()
                course_name  = course_name.replace("\n", " ").replace("\r", " ").strip()

                location = ""
                if "," in college_name:
                    location = college_name.split(",")[-1].strip()

                results.append({
                    "name":             college_name or "Unknown College",
                    "course":           course_name  or "Unknown Course",
                    "location":         location,
                    "cutoff":           round(float(cutoff), 2),
                    "probability":      round(prob, 2),
                    "chance_label":     chance,
                    "round_prediction": f"1st Round - {label}",
                })

            print(f"✅ Results: {len(results)}")

            if not results:
                return self._error("No colleges match your score for this category")

            return sorted(results, key=lambda x: x["probability"], reverse=True)

        except Exception:
            traceback.print_exc()
            return self._error("Unexpected error — see Django logs")

    def _cell(self, row, *keys):
        """
        Safe pandas Series cell reader.
        pandas Series.get(key) can return NaN for existing keys with NaN values,
        and raises KeyError for missing keys in some pandas versions.
        Always check row.index first.
        """
        for key in keys:
            if key in row.index:
                val = row[key]
                if pd.notna(val) and str(val).strip() not in ("", "-"):
                    return str(val).strip()
        return ""

    @staticmethod
    def _error(message):
        print(f"❌ {message}")
        return [{
            "name":             message,
            "course":           "-",
            "location":         "",
            "cutoff":           0.0,
            "probability":      0.0,
            "chance_label":     "Low",
            "round_prediction": "Contact administrator",
        }]