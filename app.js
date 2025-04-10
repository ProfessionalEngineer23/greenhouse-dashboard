const apiKey = "8VBQT42DSZ7SSCV3";
const channelId = "2867238";

const fieldMap = {
  Soil_Temperature: 1,
  Air_Temperature: 2,
  Humidity: 3,
  Light_Intensity: 4,
};

const predictedFiles = {
  Soil_Temperature: "https://drive.google.com/uc?export=download&id=1-6yBJmU4Iz2wfwg_opJdKgQVu4tLEALb",
  Air_Temperature: "https://drive.google.com/uc?export=download&id=1-bNzPoA-2VWE1vpka4vy4vUXxI17MqPb",
  Humidity: "https://drive.google.com/uc?export=download&id=1-U0-uaAyyoRo4gVM-tzyFypL1nNtINKQ",
  Light_Intensity: "https://drive.google.com/uc?export=download&id=1-A3_3DvK0eVOotIlZq5jyEl-lM0AWn27",
};

let chart;

document.getElementById("sensorDropdown").addEventListener("change", updateChart);
window.onload = updateChart;

async function updateChart() {
  const sensor = document.getElementById("sensorDropdown").value;

  const url = `https://api.thingspeak.com/channels/${channelId}/fields/${fieldMap[sensor]}.json?api_key=${apiKey}&results=100`;
  const response = await fetch(url);
  const data = await response.json();

  const actualTimes = data.feeds.map(f => new Date(f.created_at));
  const actualValues = data.feeds.map(f => parseFloat(f[`field${fieldMap[sensor]}`]));

  const predCsv = await fetch(predictedFiles[sensor]).then(r => r.text());
  const predLines = predCsv.split("\n").slice(1);
  const predTimes = [];
  const predValues = [];

  for (let line of predLines) {
    if (!line.trim()) continue;
    const [time, value] = line.split(",");
    predTimes.push(new Date(time));
    predValues.push(parseFloat(value));
  }

  drawChart(sensor, actualTimes, actualValues, predTimes, predValues);
}

function drawChart(label, x1, y1, x2, y2) {
  if (chart) chart.destroy();

  chart = new Chart(document.getElementById("sensorChart"), {
    type: "line",
    data: {
      labels: x1.concat(x2),
      datasets: [
        {
          label: "Actual Data",
          data: y1,
          borderColor: "blue",
          fill: false,
          tension: 0.1,
        },
        {
          label: "Predicted",
          data: new Array(y1.length).fill(null).concat(y2),
          borderColor: "red",
          borderDash: [5, 5],
          fill: false,
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { type: "time", time: { tooltipFormat: "MMM d, HH:mm" } },
        y: { beginAtZero: true },
      },
    },
  });
}
