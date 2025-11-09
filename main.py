import os
import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sklearn.preprocessing import LabelEncoder

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "kaggle")

# Load trained ML model and encoders
model = joblib.load("college_eligibility_model.pkl")
branch_encoder = joblib.load("branch_encoder.pkl")
city_encoder = joblib.load("city_encoder.pkl")

def get_supabase_data():
    """Connect to Supabase PostgreSQL and fetch dataset."""
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        with engine.connect() as conn:
            query = text(f"SELECT * FROM {SUPABASE_TABLE}")
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"Database connection error: {e}")
        return pd.DataFrame()  # return empty frame if failed


def predict_eligible_colleges_with_chances_and_related(marks: float, branch: str, city: str):
    """Predict college eligibility and chances using ML model."""
    data = get_supabase_data()

    if data.empty:
        return {"error": "Unable to fetch data from Supabase."}

    # Normalize and filter for branch & city if available
    data["branch"] = data["branch"].astype(str).str.lower()
    data["city"] = data["city"].astype(str).str.lower()
    branch, city = branch.lower(), city.lower()

    # Apply encoders
    try:
        branch_encoded = branch_encoder.transform([branch])[0]
    except Exception:
        branch_encoded = 0  # fallback if unseen label

    try:
        city_encoded = city_encoder.transform([city])[0]
    except Exception:
        city_encoded = 0

    # Prepare input DataFrame for prediction
    X_input = pd.DataFrame({
        "marks": [marks],
        "branch": [branch_encoded],
        "city": [city_encoded]
    })

    # Predict chance using model
    predicted_chance = model.predict_proba(X_input)[0][1] * 100  # assuming binary classification

    # Filter dataset based on user branch and city
    filtered_data = data[(data["branch"] == branch) & (data["city"] == city)]
    if filtered_data.empty:
        filtered_data = data  # fallback: show all if no exact match

    # Add "chance" column (for display only)
    filtered_data = filtered_data.copy()
    filtered_data["predicted_chance"] = predicted_chance

    # Return response
    result = {
        "summary": f"Predicted chance: {predicted_chance:.2f}%",
        "eligible_colleges": filtered_data[["college_name", "branch", "city", "min", "max", "predicted_chance"]].to_dict(orient="records")
    }

    return result
