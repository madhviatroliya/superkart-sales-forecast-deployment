# Flask API for serving the SuperKart sales-forecasting model
# Exposes two endpoints:
#   POST /v1/predict       -> single (online) prediction, JSON in / JSON out
#   POST /v1/predictbatch  -> batch prediction from an uploaded CSV file

import pandas as pd
import joblib
from flask import Flask, request, jsonify

# Load the serialized model pipeline once, at process start-up
MODEL_PATH = "superkart_model.joblib"
model = joblib.load(MODEL_PATH)

# Columns the model pipeline expects, in the same order used during training
FEATURE_COLUMNS = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
]

superkart_api = Flask(__name__)

@superkart_api.get("/")
def health_check():
    """Simple health-check route so we can confirm the service is up."""
    return jsonify({"status": "ok", "message": "SuperKart sales forecasting API is running."})


@superkart_api.post("/v1/predict")
def predict_single():
    """Online inference: accepts a single JSON record and returns one prediction."""
    payload = request.get_json(force=True, silent=True)

    if payload is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    missing_cols = [col for col in FEATURE_COLUMNS if col not in payload]
    if missing_cols:
        return jsonify({"error": f"Missing required fields: {missing_cols}"}), 400

    try:
        record_df = pd.DataFrame([payload], columns=FEATURE_COLUMNS)
        prediction = model.predict(record_df)[0]
        return jsonify({"Product_Store_Sales_Total": round(float(prediction), 2)}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@superkart_api.post("/v1/predictbatch")
def predict_batch():
    """Batch inference: accepts an uploaded CSV file and returns predictions for every row."""
    if "file" not in request.files:
        return jsonify({"error": "No file part named 'file' found in the request."}), 400

    file = request.files["file"]

    try:
        batch_df = pd.read_csv(file)
        missing_cols = [col for col in FEATURE_COLUMNS if col not in batch_df.columns]
        if missing_cols:
            return jsonify({"error": f"Missing required columns: {missing_cols}"}), 400

        predictions = model.predict(batch_df[FEATURE_COLUMNS])
        result = {
            str(idx): round(float(pred), 2)
            for idx, pred in zip(batch_df.index, predictions)
        }
        return jsonify(result), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    superkart_api.run(debug = True)
