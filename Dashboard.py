@app.callback(
    [Output('prediction-title', 'children'),
     Output('sensor-graph', 'figure')],
    [Input('sensor-dropdown', 'value')]
)
def update_graph(selected_feature):
    # Get actual data from ThingSpeak
    actual_url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/fields/{THINGSPEAK_FIELDS[selected_feature]}.json?api_key={THINGSPEAK_API_KEY}&results=100"
    response = requests.get(actual_url).json()

    actual_times = [entry["created_at"] for entry in response["feeds"] if entry.get(f"field{THINGSPEAK_FIELDS[selected_feature]}")]
    actual_values = [float(entry[f"field{THINGSPEAK_FIELDS[selected_feature]}"]) for entry in response["feeds"] if entry.get(f"field{THINGSPEAK_FIELDS[selected_feature]}")]

    try:
        # Load predictions from Google Drive CSV
        file_url = PREDICTED_FILES[selected_feature]
        file_response = requests.get(file_url)
        file_response.raise_for_status()
        predicted_df = pd.read_csv(io.StringIO(file_response.text))
        predicted_df['Time'] = pd.to_datetime(predicted_df['Time'])

        predicted_times = predicted_df['Time'].tolist()
        predicted_values = predicted_df['Predicted Value'].tolist()

        # Add last actual point to predicted line for smooth connection
        if actual_times and actual_values:
            predicted_times.insert(0, pd.to_datetime(actual_times[-1]))
            predicted_values.insert(0, actual_values[-1])
    except Exception as e:
        print(f"❌ Error loading predicted CSV: {e}")
        return "Error loading predicted data", {}

    # Create the plot
    fig = go.Figure()

    # Actual Data
    fig.add_trace(go.Scatter(
        x=actual_times,
        y=actual_values,
        mode='lines+markers',
        name="Actual Data",
        line=dict(color='blue'),
        hovertemplate='Time: %{x}<br>Value: %{y}<br><b>Type: Actual</b><extra></extra>'
    ))

    # Predicted Data
    fig.add_trace(go.Scatter(
        x=predicted_times,
        y=predicted_values,
        mode='lines+markers',
        name="Predicted Future",
        line=dict(color='red', dash='dash'),
        hovertemplate='Time: %{x}<br>Value: %{y}<br><b>Type: Predicted</b><extra></extra>'
    ))

    # Vertical divider
    if actual_times:
        divider_time = pd.to_datetime(actual_times[-1])
        fig.add_shape(
            type="line",
            x0=divider_time,
            y0=min(actual_values + predicted_values) * 0.9,
            x1=divider_time,
            y1=max(actual_values + predicted_values) * 1.1,
            line=dict(color="gray", dash="dot", width=1)
        )

    # Layout
    fig.update_layout(
        title=f"Sensor vs AI Prediction: {SENSOR_LABELS[selected_feature]}",
        xaxis_title="Time",
        yaxis_title=SENSOR_LABELS[selected_feature],
        template="plotly_white",
        yaxis=dict(range=[
            min(actual_values + predicted_values) * 0.9,
            max(actual_values + predicted_values) * 1.1
        ]),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black')
    )

    return f"{SENSOR_LABELS[selected_feature]} - Actual vs Predicted", fig
