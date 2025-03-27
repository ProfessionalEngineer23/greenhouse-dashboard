import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import requests

# ThingSpeak API configuration
THINGSPEAK_CHANNEL_ID = "2867238"
THINGSPEAK_API_KEY = "8VBQT42DSZ7SSCV3"

# Mapping each sensor name to its corresponding ThingSpeak field number
THINGSPEAK_FIELDS = {
    'Soil_Temperature': 1,
    'Air_Temperature': 2,
    'Humidity': 3,
    'Light_Intensity': 4
}

# Public Google Drive CSV file URLs for AI-predicted values
PREDICTED_FILES = {
    'Soil_Temperature': "https://drive.google.com/uc?export=download&id=1-A3_3DvK0eVOotIlZq5jyEl-lM0AWn27",
    'Air_Temperature': "https://drive.google.com/uc?export=download&id=1-bNzPoA-2VWE1vpka4vy4vUXxI17MqPb",
    'Humidity': "https://drive.google.com/uc?export=download&id=1-U0-uaAyyoRo4gVM-tzyFypL1nNtINKQ",
    'Light_Intensity': "https://drive.google.com/uc?export=download&id=1-6yBJmU4Iz2wfwg_opJdKgQVu4tLEALb"
}

# Labels used for display on the dashboard
SENSOR_LABELS = {
    'Soil_Temperature': "Soil Temperature (°C)",
    'Air_Temperature': "Air Temperature (°C)",
    'Humidity': "Humidity (%)",
    'Light_Intensity': "Light Intensity (lux)"
}

# Initialize the Dash application
app = dash.Dash(__name__)
server = app.server  # Expose the server object for deployment (e.g., with gunicorn)

# Define the layout of the dashboard
app.layout = html.Div(style={'backgroundColor': 'green', 'color': 'black', 'padding': '10px'}, children=[
    html.H1("Greenhouse AI & Sensor Dashboard", style={'textAlign': 'center'}),

    # Dropdown menu to select sensor type
    dcc.Dropdown(
        id='sensor-dropdown',
        options=[{'label': label, 'value': key} for key, label in SENSOR_LABELS.items()],
        value='Air_Temperature',  # Default selection
        style={'width': '50%', 'margin': 'auto'}
    ),

    # Title and graph output
    html.Div(id='prediction-title', style={'textAlign': 'center'}),
    dcc.Graph(id='sensor-graph', style={'height': '80vh'})
])

# Define callback to update the graph when a sensor is selected
@app.callback(
    [Output('prediction-title', 'children'),
     Output('sensor-graph', 'figure')],
    [Input('sensor-dropdown', 'value')]
)
def update_graph(selected_feature):
    # Fetch actual sensor data from ThingSpeak using API
    actual_url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/fields/{THINGSPEAK_FIELDS[selected_feature]}.json?api_key={THINGSPEAK_API_KEY}&results=100"
    response = requests.get(actual_url).json()

    # Parse actual data timestamps and values
    actual_times = [entry["created_at"] for entry in response["feeds"] if entry[f"field{THINGSPEAK_FIELDS[selected_feature]}"]]
    actual_values = [float(entry[f"field{THINGSPEAK_FIELDS[selected_feature]}"]) for entry in response["feeds"] if entry[f"field{THINGSPEAK_FIELDS[selected_feature]}"]]

    # Load predicted data from Google Drive CSV
    try:
        predicted_df = pd.read_csv(PREDICTED_FILES[selected_feature])
        predicted_df['Time'] = pd.to_datetime(predicted_df['Time'])
        predicted_time = predicted_df['Time']
        predicted_values = predicted_df['Predicted Value']
    except Exception as e:
        return "Error loading predicted data", {}

    # Create graph
    fig = go.Figure()

    # Add actual data trace (blue)
    fig.add_trace(go.Scatter(
        x=actual_times, y=actual_values,
        mode='lines+markers', name="Actual Data", line=dict(color='blue')
    ))

    # Add predicted data trace (red dashed line)
    fig.add_trace(go.Scatter(
        x=predicted_time, y=predicted_values,
        mode='lines+markers', name="Predicted Future", line=dict(color='red', dash='dash')
    ))

    # Set Y-axis range with padding
    y_min = min(min(actual_values), min(predicted_values)) * 0.9
    y_max = max(max(actual_values), max(predicted_values)) * 1.1

    # Final layout formatting
    fig.update_layout(
        title=f"Sensor vs AI Prediction: {SENSOR_LABELS[selected_feature]}",
        xaxis_title="Time",
        yaxis_title=SENSOR_LABELS[selected_feature],
        template="plotly_dark",
        yaxis=dict(range=[y_min, y_max])
    )

    # Return title and figure
    return f"{SENSOR_LABELS[selected_feature]} - Actual vs Predicted", fig

# Run app locally if script is executed directly
if __name__ == '__main__':
    app.run_server(debug=True)
