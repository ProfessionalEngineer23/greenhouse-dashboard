import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import requests
import io

# ThingSpeak Config
THINGSPEAK_CHANNEL_ID = "2867238"
THINGSPEAK_API_KEY = "8VBQT42DSZ7SSCV3"

# 🔁 Swapped Light and Soil field mappings
THINGSPEAK_FIELDS = {
    'Light_Intensity': 1,      # was Soil_Temperature
    'Air_Temperature': 2,
    'Humidity': 3,
    'Soil_Temperature': 4      # was Light_Intensity
}

PREDICTED_FILES = {
    'Soil_Temperature': "https://drive.google.com/uc?export=download&id=1-6yBJmU4Iz2wfwg_opJdKgQVu4tLEALb",  # was Light
    'Air_Temperature': "https://drive.google.com/uc?export=download&id=1-bNzPoA-2VWE1vpka4vy4vUXxI17MqPb",
    'Humidity': "https://drive.google.com/uc?export=download&id=1-U0-uaAyyoRo4gVM-tzyFypL1nNtINKQ",
    'Light_Intensity': "https://drive.google.com/uc?export=download&id=1-A3_3DvK0eVOotIlZq5jyEl-lM0AWn27"   # was Soil
}

SENSOR_LABELS = {
    'Soil_Temperature': "Soil Temperature (°C)",
    'Air_Temperature': "Air Temperature (°C)",
    'Humidity': "Humidity (%)",
    'Light_Intensity': "Light Intensity (lux)"
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
    actual_url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/fields/{THINGSPEAK_FIELDS[selected_feature]}.json?api_key={THINGSPEAK_API_KEY}&results=100"
    response = requests.get(actual_url).json()

    actual_times = [pd.to_datetime(entry["created_at"]).tz_localize(None) for entry in response["feeds"] if entry.get(f"field{THINGSPEAK_FIELDS[selected_feature]}")]
    actual_values = [float(entry[f"field{THINGSPEAK_FIELDS[selected_feature]}"]) for entry in response["feeds"] if entry.get(f"field{THINGSPEAK_FIELDS[selected_feature]}")]

    try:
        file_url = PREDICTED_FILES[selected_feature]
        file_response = requests.get(file_url)
        file_response.raise_for_status()
        predicted_df = pd.read_csv(io.StringIO(file_response.text))
        predicted_df['Time'] = pd.to_datetime(predicted_df['Time'])
        predicted_df['Time'] = predicted_df['Time'].dt.tz_localize(None)

        predicted_times = predicted_df['Time'].tolist()
        predicted_values = predicted_df['Predicted Value'].tolist()

    except Exception as e:
        print(f"❌ Error loading predicted CSV: {e}")
        return "Error loading predicted data", {}

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=actual_times,
        y=actual_values,
        mode='lines+markers',
        name="Actual Data",
        line=dict(color='blue'),
        hovertemplate='Time: %{x}<br>Value: %{y}<br><b>Type: Actual</b><extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=predicted_times,
        y=predicted_values,
        mode='lines+markers',
        name="Predicted Future",
        line=dict(color='red', dash='dash'),
        hovertemplate='Time: %{x}<br>Value: %{y}<br><b>Type: Predicted</b><extra></extra>'
    ))

    if actual_times and predicted_times:
        divider_time = predicted_times[0]
        fig.add_shape(
            type="line",
            x0=divider_time,
            y0=min(actual_values + predicted_values) * 0.9,
            x1=divider_time,
            y1=max(actual_values + predicted_values) * 1.1,
            line=dict(color="gray", dash="dot", width=1)
        )

    x_min = min(actual_times + predicted_times)
    x_max = max(actual_times + predicted_times)
    default_range_start = x_max - pd.Timedelta(hours=1)

    fig.update_layout(
        title=f"Sensor vs AI Prediction: {SENSOR_LABELS[selected_feature]}",
        xaxis_title="Time",
        yaxis_title=SENSOR_LABELS[selected_feature],
        template="plotly_white",
        yaxis=dict(range=[
            min(actual_values + predicted_values) * 0.9,
            max(actual_values + predicted_values) * 1.1
        ]),
        xaxis=dict(
            tickformat="%b %d\n%H:%M",
            showgrid=True,
            rangeslider_visible=True,
            range=[default_range_start, x_max]
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black')
    )

    return f"{SENSOR_LABELS[selected_feature]} - Actual vs Predicted", fig

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=10000)
