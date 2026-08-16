# Streamlit UI for the SuperKart sales-forecasting model
# Talks to the Flask backend (running in its own container, on the same
# Docker network) for both single-record and batch (CSV) predictions.

import os
import requests
import pandas as pd
import streamlit as st

BACKEND_URL = "http://backend:7860"
st.set_page_config(page_title="SuperKart Sales Forecast", layout="centered")
st.title("🛒 SuperKart Sales Forecasting")
st.write(
    "Estimate the total sales revenue a product will generate at a given "
    "store, using the deployed SuperKart forecasting model."
)
tab_single, tab_batch = st.tabs(["Single Prediction", "Batch Prediction"])

# Single / online prediction
with tab_single:
    st.subheader("Enter product & store details")
    col1, col2 = st.columns(2)
    with col1:
        product_weight = st.number_input("Product Weight", min_value=0.0, 
                                         value=12.5)
        product_sugar_content = st.selectbox(
            "Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"]
        )
        product_allocated_area = st.number_input(
            "Product Allocated Area", min_value=0.0, max_value=1.0, value=0.05
        )
        product_mrp = st.number_input("Product MRP", min_value=0.0, value=120.0)
        product_id_char = st.selectbox("Product Id Prefix", ["FD", "DR", "NC"])

    with col2:
        store_size = st.selectbox("Store Size", ["High", "Medium", "Small"])
        store_location_city_type = st.selectbox(
            "Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"]
        )
        store_type = st.selectbox(
            "Store Type",
            ["Departmental Store", "Supermarket Type1", "Supermarket Type2", 
             "Food Mart"],
        )
        store_age_years = st.number_input("Store Age (Years)", min_value=0, 
                                          value=15)
        product_type_category = st.selectbox(
            "Product Type Category", ["Perishables", "Non Perishables"]
        )

    if st.button("Predict Sales", key="single_predict"):
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar_content,
            "Product_Allocated_Area": product_allocated_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_location_city_type,
            "Store_Type": store_type,
            "Product_Id_char": product_id_char,
            "Store_Age_Years": store_age_years,
            "Product_Type_Category": product_type_category,
        }
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload,
                                     timeout=30)
            if response.status_code == 200:
                result = response.json()
                st.success(f"Predicted Total Sales: {result['Product_Store_Sales_Total']}")
            else:
                st.error(f"API Error ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the backend API: {exc}")

# Batch prediction
with tab_batch:
    st.subheader("Upload a CSV file for batch predictions")
    st.caption(
        "The file must contain the columns: Product_Weight, Product_Sugar_Content, "
        "Product_Allocated_Area, Product_MRP, Store_Size, Store_Location_City_Type, "
        "Store_Type, Product_Id_char, Store_Age_Years, Product_Type_Category."
    )

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        preview_df = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded data:")
        st.dataframe(preview_df.head())

        if st.button("Run Batch Prediction", key="batch_predict"):
            uploaded_file.seek(0)
            files = {"file": uploaded_file.getvalue()}
            try:
                response = requests.post(f"{BACKEND_URL}/v1/predictbatch", files=files, timeout=60)
                if response.status_code == 200:
                    preds = response.json()
                    preview_df["Predicted_Sales"] = preview_df.index.astype(str).map(preds)
                    st.success("Batch predictions complete.")
                    st.dataframe(preview_df)
                    st.download_button(
                        "Download Predictions as CSV",
                        preview_df.to_csv(index=False).encode("utf-8"),
                        "superkart_predictions.csv",
                        "text/csv",
                    )
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not reach the backend API: {exc}")
