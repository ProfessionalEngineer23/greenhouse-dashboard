const THINGSPEAK_CHANNEL_ID = "2867238";
const THINGSPEAK_API_KEY = "8VBQT42DSZ7SSCV3";

const PREDICTED_FILES = {
  "Soil_Temperature": "https://drive.google.com/uc?export=download&id=1-6yBJmU4Iz2wfwg_opJdKgQVu4tLEALb",
  "Air_Temperature": "https://drive.google.com/uc?export=download&id=1-bNzPoA-2VWE1vpka4vy4vUXxI17MqPb",
  "Humidity": "https://drive.google.com/uc?export=download&id=1-U0-uaAyyoRo4gVM-tzyFypL1nNtINKQ",
  "Light_Intensity": "https://drive.google.com/uc?export=download&id=1-A3_3DvK0eVOotIlZq5jyEl-lM0AWn27"
};

const FIELD_MAP = {
  "Soil_Temperature": 1,
  "Air_Temperature": 2,
  "Humidity": 3,
  "Light_Intensity": 4
};

async function fetchCSV(url) {
  const response = await fetch(url);
  const text = await response.text();
  const rows = text.trim().split("\n").slice(1);
  return rows.map(r => {
    const [time, value] = r.split(",");
    return { x: new Date(time), y: parseFloat(value) };
  });
}

async function fetchThingSpeakData(fieldNum) {
  const url = `https://api.thingspeak.com/channels/${THINGSPEAK_CHANNEL_ID}/fields/${fieldNum}.json?api_key=${THINGSPEAK_API_KEY}&results=100`;
  const response = await fetch(url);
  const json = await response.json();
  return json.feeds.map(entry => ({
    x: new Date(entry.created_at),
    y: parseFloat(entry[`field${fieldNum}`])
  })).filter(d => !isNaN(d.y));
}

async function updateGraph(feature) {
  const actual = await fetchThingSpeakData(FIELD_MAP[feature]);
  const predicted = await fetchCSV(PREDICTED_FILES[feature]);

  const layout = {
    title: `Sensor vs AI Prediction: ${feature.replace("_", " ")}`,
    xaxis: { title: "Time" },
    yaxis: { title: feature },
    margin: { t: 50 }
  };

  Plotly.newPlot("plot", [
    {
      x: actual.map(d => d.x),
      y: actual.map(d => d.y),
      mode: 'lines+markers',
      name: 'Actual Data',
      line: { color: 'blue' }
    },
    {
      x: predicted.map(d => d.x),
      y: predicted.map(d => d.y),
      mode: 'lines+markers',
      name: 'Predicted',
      line: { color: 'red', dash: 'dash' }
    }
  ], layout);
}

document.getElementById("dropdown").addEventListener("change", e => {
  updateGraph(e.target.value);
});

updateGraph("Air_Temperature");
