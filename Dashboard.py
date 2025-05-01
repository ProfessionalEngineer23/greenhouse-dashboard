import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import requests
import io
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# ThingSpeak Config
THINGSPEAK_CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID")
THINGSPEAK_API_KEY = os.getenv("THINGSPEAK_API_KEY")

# ✅ Updated mappings including Fan
THINGSPEAK_FIELDS = {
    'Soil_Temperature': 1,
    'Air_Temperature': 2,
    'Humidity': 3,
    'Light_Intensity': 4,
    'Fan': 5
}

# ✅ Updated predicted file mapping
PREDICTED_FILES = {
    'Soil_Temperature': "https://drive.google.com/uc?export=download&id=1-6yBJmU4Iz2wfwg_opJdKgQVu4tLEALb",
    'Air_Temperature': "https://drive.google.com/uc?export=download&id=1-bNzPoA-2VWE1vpka4vy4vUXxI17MqPb",
    'Humidity': "https://drive.google.com/uc?export=download&id=1-U0-uaAyyoRo4gVM-tzyFypL1nNtINKQ",
    'Light_Intensity': "https://drive.google.com/uc?export=download&id=1-A3_3DvK0eVOotIlZq5jyEl-lM0AWn27"
}

SENSOR_LABELS = {
    'Soil_Temperature': "Soil Temperature (°C)",
    'Air_Temperature': "Air Temperature (°C)",
    'Humidity': "Humidity (%)",
    'Light_Intensity': "Light Intensity (lux)",
    'Fan': "Fan Status (On = 1, Off = 0)"
}

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(style={'backgroundColor': 'white', 'color': 'black', 'padding': '10px'}, children=[
    html.H1("Greenhouse AI & Sensor Dashboard", style={'textAlign': 'center'}),

    dcc.Dropdown(
        id='sensor-dropdown',
        options=[{'label': label, 'value': key} for key, label in SENSOR_LABELS.items()],
        value='Air_Temperature',
        style={'width': '50%', 'margin': 'auto'}
    ),

    html.Div(id='prediction-title', style={'textAlign': 'center'}),
    dcc.Graph(id='sensor-graph', style={'height': '80vh'}),

    dcc.Interval(
        id='interval-component',
        interval=60 * 1000,
        n_intervals=0
    )
])

@app.callback(
    [Output('prediction-title', 'children'),
     Output('sensor-graph', 'figure')],
    [Input('sensor-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_graph(selected_feature, n_intervals):
    field_id = THINGSPEAK_FIELDS[selected_feature]
    actual_url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/fields/{field_id}.json?api_key={THINGSPEAK_API_KEY}&results=100"
    response = requests.get(actual_url).json()

    actual_times = [pd.to_datetime(entry["created_at"]).tz_localize(None)
                    for entry in response["feeds"] if entry.get(f"field{field_id}")]
    actual_values = [float(entry[f"field{field_id}"])
                     for entry in response["feeds"] if entry.get(f"field{field_id}")]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=actual_times,
        y=actual_values,
        mode='lines+markers',
        name="Actual Data",
        line=dict(color='green' if selected_feature == 'Fan' else 'blue'),
        hovertemplate='Time: %{x}<br>Value: %{y}<extra></extra>'
    ))

    # Only show predicted data if not Fan
    if selected_feature != 'Fan':
        try:
            file_url = PREDICTED_FILES[selected_feature]
            file_response = requests.get(file_url)
            file_response.raise_for_status()
            predicted_df = pd.read_csv(io.StringIO(file_response.text))
            predicted_df['Time'] = pd.to_datetime(predicted_df['Time']).dt.tz_localize(None)

            fig.add_trace(go.Scatter(
                x=predicted_df['Time'],
                y=predicted_df['Predicted Value'],
                mode='lines+markers',
                name="Predicted Future",
                line=dict(color='red', dash='dash'),
                hovertemplate='Time: %{x}<br>Value: %{y}<br><b>Type: Predicted</b><extra></extra>'
            ))

            fig.add_shape(
                type="line",
                x0=predicted_df['Time'].iloc[0],
                y0=min(actual_values + predicted_df['Predicted Value'].tolist()) * 0.9,
                x1=predicted_df['Time'].iloc[0],
                y1=max(actual_values + predicted_df['Predicted Value'].tolist()) * 1.1,
                line=dict(color="gray", dash="dot", width=1)
            )

        except Exception as e:
            print(f"❌ Error loading predicted CSV: {e}")

    yaxis_title = SENSOR_LABELS[selected_feature]
    y_min = min(actual_values) - 1 if selected_feature == 'Fan' else min(actual_values) * 0.9
    y_max = max(actual_values) + 1 if selected_feature == 'Fan' else max(actual_values) * 1.1

    fig.update_layout(
        title=f"{SENSOR_LABELS[selected_feature]} - Actual{' vs Predicted' if selected_feature != 'Fan' else ''}",
        xaxis_title="Time",
        yaxis_title=yaxis_title,
        template="plotly_white",
        yaxis=dict(range=[y_min, y_max]),
        xaxis=dict(tickformat="%b %d\n%H:%M", showgrid=True, rangeslider_visible=True),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black')
    )

    return f"{SENSOR_LABELS[selected_feature]}", fig

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=10000)
