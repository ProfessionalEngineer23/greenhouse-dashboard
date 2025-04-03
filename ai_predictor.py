import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import requests
import io

# ThingSpeak API configuration
THINGSPEAK_CHANNEL_ID = "2867238"
THINGSPEAK_API_KEY = "8VBQT42DSZ7SSCV3"
THINGSPEAK_UPDATE_URL = "https://api.thingspeak.com/update?api_key=R1ZTW11SA2559MEB&field1=0"

# Mapping sensor names to their ThingSpeak field numbers
THINGSPEAK_FIELDS = {
    'Soil_Temperature': 1,
    'Air_Temperature': 2,
    'Humidity': 3,
    'Light_Intensity': 4
}

# Public Google Drive links to CSV files for AI-predicted data
PREDICTED_FILES = {
    'Soil_Temperature': "https://drive.google.com/uc?export=download&id=1-A3_3DvK0eVOotIlZq5jyEl-lM0AWn27",
    'Air_Temperature': "https://drive.google.com/uc?export=download&id=1-bNzPoA-2VWE1vpka4vy4vUXxI17MqPb",
    'Humidity': "https://drive.google.com/uc?export=download&id=1-U0-uaAyyoRo4gVM-tzyFypL1nNtINKQ",
    'Light_Intensity': "https://drive.google.com/uc?export=download&id=1-6yBJmU4Iz2wfwg_opJdKgQVu4tLEALb"
}

# Display labels for each sensor
SENSOR_LABELS = {
    'Soil_Temperature': "Soil Temperature (°C)",
    'Air_Temperature': "Air Temperature (°C)",
    'Humidity': "Humidity (%)",
    'Light_Intensity': "Light Intensity (lux)"
}

# Fetch actual sensor data from ThingSpeak
def fetch_actual_data(selected_feature):
    url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/fields/{THINGSPEAK_FIELDS[selected_feature]}.json?api_key={THINGSPEAK_API_KEY}&results=100"
    response = requests.get(url).json()
    actual_times = [entry["created_at"] for entry in response["feeds"] if entry.get(f"field{THINGSPEAK_FIELDS[selected_feature]}")]
    actual_values = [float(entry[f"field{THINGSPEAK_FIELDS[selected_feature]}"]) for entry in response["feeds"] if entry.get(f"field{THINGSPEAK_FIELDS[selected_feature]}")]
    return actual_times, actual_values

# Fetch predicted data from public Google Drive CSV
def fetch_predicted_data(selected_feature):
    try:
        file_url = PREDICTED_FILES[selected_feature]
        file_response = requests.get(file_url)
        file_response.raise_for_status()
        predicted_df = pd.read_csv(io.StringIO(file_response.text))
        predicted_df['Time'] = pd.to_datetime(predicted_df['Time'])
        return predicted_df['Time'], predicted_df['Predicted Value']
    except Exception as e:
        print(f"Failed to load predicted CSV: {e}")
        return [], []

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server

# Define app layout
app.layout = html.Div(style={'backgroundColor': 'white', 'color': 'black', 'padding': '10px'}, children=[
    html.H1("Greenhouse AI & Sensor Dashboard", style={'textAlign': 'center'}),

    dcc.Dropdown(
        id='sensor-dropdown',
        options=[{'label': label, 'value': key} for key, label in SENSOR_LABELS.items()],
        value='Air_Temperature',
        style={'width': '50%', 'margin': 'auto'}
    ),

    html.Div(id='prediction-title', style={'textAlign': 'center'}),

    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # 1 minute
        n_intervals=0
    ),

    dcc.Graph(id='sensor-graph', style={'height': '80vh'})
])

# Graph update logic
@app.callback(
    [Output('prediction-title', 'children'),
     Output('sensor-graph', 'figure')],
    [Input('sensor-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_graph(selected_feature, n):
    actual_times, actual_values = fetch_actual_data(selected_feature)
    predicted_time, predicted_values = fetch_predicted_data(selected_feature)

    if not actual_times or len(predicted_time) == 0:
        return "Error loading data", {}

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=actual_times, y=actual_values,
        mode='lines+markers', name="Actual Data", line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=predicted_time, y=predicted_values,
        mode='lines+markers', name="Predicted Future", line=dict(color='red', dash='dash')
    ))

    y_min = min(min(actual_values), min(predicted_values)) * 0.9
    y_max = max(max(actual_values), max(predicted_values)) * 1.1

    fig.update_layout(
        title=f"Sensor vs AI Prediction: {SENSOR_LABELS[selected_feature]}",
        xaxis_title="Time",
        yaxis_title=SENSOR_LABELS[selected_feature],
        template="plotly_white",
        yaxis=dict(range=[y_min, y_max]),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black')
    )

    return f"{SENSOR_LABELS[selected_feature]} - Actual vs Predicted", fig

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=10000)
