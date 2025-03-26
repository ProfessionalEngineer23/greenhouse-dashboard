import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import os

# 🟢 Windows Google Drive Path (Change if needed)
GOOGLE_DRIVE_PATH = r"G:\My Drive\Colab Notebooks\CSV_DATA"

# Sensor Labels for Better Readability
SENSOR_LABELS = {
    'Soil_Temperature': "Soil Temperature (°C)",
    'Air_Temperature': "Air Temperature (°C)",
    'Humidity': "Humidity (%)",
    'Light_Intensity': "Light Intensity (lux)"
}

# Initialize Dash App
app = dash.Dash(__name__)

app.layout = html.Div(style={'backgroundColor': 'green', 'color': 'Black', 'padding': '10px'}, children=[
    html.H1("Greenhouse AI Predictions Dashboard", style={'textAlign': 'center'}),

    dcc.Dropdown(
        id='sensor-dropdown',
        options=[{'label': label, 'value': key} for key, label in SENSOR_LABELS.items()],
        value='Air_Temperature',  # Default sensor selection
        style={'width': '50%', 'margin': 'auto'}
    ),

    html.Div(id='prediction-title', style={'textAlign': 'center'}),

    dcc.Graph(id='prediction-graph', style={'height': '80vh'})
])

@app.callback(
    [Output('prediction-title', 'children'),
     Output('prediction-graph', 'figure')],
    [Input('sensor-dropdown', 'value')]
)
def update_graph(selected_feature):
    """Load actual & predicted CSV data from Google Drive and update graph."""

    actual_file = os.path.join(GOOGLE_DRIVE_PATH, "Actual_Sensor_Data.csv")  # 🔹 Actual data file
    predicted_file = os.path.join(GOOGLE_DRIVE_PATH, f"Predicted_{selected_feature}.csv")  # 🔹 AI Predictions

    if os.path.exists(actual_file) and os.path.exists(predicted_file):
        # Load actual sensor data
        actual_df = pd.read_csv(actual_file)
        actual_df['Time'] = pd.to_datetime(actual_df['Time'])  # Convert time to datetime

        # Load AI prediction data
        predicted_df = pd.read_csv(predicted_file)
        predicted_df['Time'] = pd.to_datetime(predicted_df['Time'])  # Convert time to datetime

        # Define sensor label
        y_axis_label = SENSOR_LABELS[selected_feature]

        # Create graph with actual and predicted values
        fig = go.Figure()

        # Plot actual sensor data
        fig.add_trace(go.Scatter(
            x=actual_df['Time'], y=actual_df[selected_feature],
            mode='lines+markers', name="Actual Data", line=dict(color='blue')
        ))

        # Plot AI predicted data (future)
        fig.add_trace(go.Scatter(
            x=predicted_df['Time'], y=predicted_df['Predicted Value'],
            mode='lines+markers', name="Predicted Future", line=dict(color='red', dash='dash')
        ))

        # Ensure proper Y-axis scaling
        y_min = min(actual_df[selected_feature].min(), predicted_df["Predicted Value"].min()) * 0.9
        y_max = max(actual_df[selected_feature].max(), predicted_df["Predicted Value"].max()) * 1.1

        # Formatting
        fig.update_layout(
            title=f"AI Prediction for {selected_feature}",
            xaxis_title="Time",
            yaxis_title=y_axis_label,
            template="plotly_dark",
            yaxis=dict(range=[y_min, y_max])
        )

        return f"Predictions for {selected_feature}", fig

    else:
        return f"No Data Available for {selected_feature}", {}

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
