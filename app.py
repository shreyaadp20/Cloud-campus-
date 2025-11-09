from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import traceback

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "templates")
DATA_PATH = os.path.join(BASE_DIR, "..", "kaggle_raw.csv")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
CORS(app)

# --- Load dataset once ---
try:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    # Normalize some expected columns
    for col in ["branch", "city", "mean"]:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in CSV.")
    print(f"✅ Loaded dataset: {len(df)} rows from {DATA_PATH}")
except Exception as e:
    print("❌ Failed to load dataset:", e)
    df = pd.DataFrame()  # keep app up; return error on call


# ---------- Helpers ----------
def compute_results(marks: float, branch: str, city: str):
    if df.empty:
        return {"error": "Dataset not loaded. Check kaggle_raw.csv path/columns."}

    # filter (case-insensitive, allows partial match)
    filtered = df.copy()
    if branch:
        filtered = filtered[filtered["branch"].astype(str).str.lower().str.contains(branch.lower(), na=False)]
    if city:
        filtered = filtered[filtered["city"].astype(str).str.lower().str.contains(city.lower(), na=False)]

    if filtered.empty:
        return {"eligible_colleges": []}

    # simple chance: closer mean cutoff to marks → higher chance
    filtered = filtered.copy()
    filtered["chances"] = 100 - (filtered["mean"].astype(float) - float(marks)).abs()
    filtered["chances"] = filtered["chances"].clip(lower=0, upper=100)

    top = (
        filtered.sort_values("chances", ascending=False)
        .head(10)[["college_name", "branch", "city", "chances"]]
        .to_dict(orient="records")
    )
    return {"eligible_colleges": top}


# ---------- Routes ----------
@app.route("/")
def home():
    return render_template("predict.html")

# main endpoint
@app.route("/predict_colleges", methods=["POST"])
def predict_colleges():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"error": "Request body must be JSON."}), 400

        marks = payload.get("marks")
        branch = (payload.get("branch") or "").strip()
        city = (payload.get("city") or "").strip()

        if marks is None or branch == "" or city == "":
            return jsonify({"error": "Missing fields: marks, branch, city are required."}), 400

        marks = float(marks)
        res = compute_results(marks, branch, city)
        return jsonify(res)
    except Exception:
        app.logger.error("Predict error:\n%s", traceback.format_exc())
        return jsonify({"error": "Internal error computing prediction."}), 500

# alias for older frontend calls
@app.route("/api/predict_colleges", methods=["POST"])
def predict_colleges_alias():
    return predict_colleges()

# helpful GET for quick ping
@app.route("/predict_colleges", methods=["GET"])
def predict_colleges_get():
    return jsonify({"ok": True, "message": "POST JSON to this endpoint."})

# JSON error pages so the frontend never gets HTML
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500


#if __name__ == "__main__":
   # print(f"Template dir: {os.path.abspath(TEMPLATE_DIR)}")
    #print(f"CSV path    : {os.path.abspath(DATA_PATH)}")
    #app.run(debug=True)
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
