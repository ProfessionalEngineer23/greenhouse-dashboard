# Install schedule if not already installed
!pip install schedule

# --- IMPORT LIBRARIES ---
import os
import pandas as pd
import numpy as np
import time
import schedule
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from datetime import datetime
from google.colab import drive
import requests
import hashlib

# --- MOUNT GOOGLE DRIVE ---
drive.mount('/content/drive')

# --- PATHS ---
DATA_PATH = "/content/drive/MyDrive/Colab Notebooks/CSV_DATA/Master_Sensor_Data.csv"
SAVE_DIR = "/content/drive/MyDrive/Colab Notebooks/CSV_DATA"
os.makedirs(SAVE_DIR, exist_ok=True)

# --- THINGSPEAK CONFIG (OPTIONAL FOR FUTURE APPEND) ---
CHANNEL_ID = "2867238"
READ_API_KEY = "8VBQT42DSZ7SSCV3"

# --- SENSOR FIELD LABELS ---
COLUMN_MAP = {
    'field1': 'Soil_Temperature',
    'field2': 'Air_Temperature',
    'field3': 'Humidity',
    'field4': 'Light_Intensity'
}

# --- HASH FOR DUPLICATE CHECKING ---
last_hash = None

def hash_dataframe(df):
    """Create a hash to detect changes in data"""
    return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()

def load_master_data():
    """Load cleaned sensor data from CSV"""
    try:
        df = pd.read_csv(DATA_PATH)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.set_index('created_at', inplace=True)

        expected_cols = ['Soil_Temperature', 'Air_Temperature', 'Humidity', 'Light_Intensity']
        if not all(col in df.columns for col in expected_cols):
            print("⚠️ CSV is missing one or more expected sensor columns.")
            return None

        df = df[expected_cols].dropna()
        df['time_seconds'] = (df.index - df.index.min()).total_seconds()

        print(f"✅ Loaded {len(df)} rows after filtering")
        print("📊 Columns:", df.columns.tolist())
        return df
    except Exception as e:
        print(f"❌ Error loading master data: {e}")
        return None

def train_and_predict(df, feature):
    """Train a model and predict future values"""
    cleaned = df.dropna(subset=[feature])
    if len(cleaned) < 2:
        print(f"⚠️ Not enough valid data to train for {feature}")
        return None

    X = cleaned[['time_seconds']].values
    y = cleaned[feature].values
    model = LinearRegression().fit(X, y)

    future_times = np.array([(cleaned['time_seconds'].max() + i * 60) for i in range(1, 6)]).reshape(-1, 1)
    predictions = model.predict(future_times)

    return pd.DataFrame({
        'Time': [cleaned.index.max() + pd.Timedelta(minutes=i) for i in range(1, 6)],
        'Predicted Value': predictions
    })

def save_predictions(pred_df, feature):
    """Save predictions to CSV"""
    if pred_df is None or pred_df.empty:
        print(f"⚠️ No predictions to save for {feature}")
        return
    filename = f"Predicted_{feature}.csv"
    save_path = os.path.join(SAVE_DIR, filename)
    pred_df.to_csv(save_path, index=False)
    print(f"✅ Saved predictions to {save_path}")

def save_graph(feature, df, predictions):
    """Save a plot of actual vs predicted"""
    if predictions is None or predictions.empty:
        print(f"⚠️ Skipping graph for {feature} (no predictions)")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df[feature], label="Actual Data", marker='o')
    plt.plot(predictions["Time"], predictions["Predicted Value"], linestyle="dashed", color="red", marker='x', label="Predicted Future")

    plt.xlabel("Time")
    plt.ylabel(feature)
    plt.legend()
    plt.title(f"AI Prediction for {feature}")
    plt.xticks(rotation=45)

    filename = f"Predicted_{feature}.png"
    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved graph to {save_path}")

def run_ai_update():
    """Main routine: load, train, save"""
    global last_hash
    df = load_master_data()
    if df is None or df.empty:
        print("⚠️ No valid data to process.")
        return

    current_hash = hash_dataframe(df)
    if current_hash == last_hash:
        print("⏩ No new data. Skipping update.")
        return
    last_hash = current_hash

    for feature in ['Soil_Temperature', 'Air_Temperature', 'Humidity', 'Light_Intensity']:
        if feature in df.columns:
            predictions = train_and_predict(df, feature)
            save_predictions(predictions, feature)
            save_graph(feature, df, predictions)

# --- SCHEDULING LOOP ---
schedule.every(5).minutes.do(run_ai_update)
print("📅 AI auto-update is scheduled every 5 minutes.")

# Run once immediately to test
run_ai_update()

# Continuous loop (uncomment if needed)
while True:
     schedule.run_pending()
     time.sleep(1)
