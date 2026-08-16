import json
import sqlite3
import threading
import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import paho.mqtt.client as mqtt

DB_NAME = "sensor_data.db"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "esp32/GENES/data"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS telemetry
                 (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, temperature REAL, humidity REAL, light INTEGER, distance REAL)''')
    conn.commit()
    conn.close()

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO telemetry (temperature, humidity, light, distance) VALUES (?, ?, ?, ?)",
                  (data.get('temperature'), data.get('humidity'), data.get('light'), data.get('distance')))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving telemetry:", e)

def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()

init_db()
threading.Thread(target=start_mqtt, daemon=True).start()

app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Lab 5: Real-Time Telemetry Dashboard"),
    dcc.Interval(id='graph-update', interval=2000, n_intervals=0),
    html.Div([
        dcc.Graph(id='temp-graph'), dcc.Graph(id='hum-graph'),
        dcc.Graph(id='light-graph'), dcc.Graph(id='dist-graph')
    ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr'})
])

@app.callback(
    [Output('temp-graph', 'figure'), Output('hum-graph', 'figure'),
     Output('light-graph', 'figure'), Output('dist-graph', 'figure')],
    [Input('graph-update', 'n_intervals')]
)
def update_graphs(n):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT timestamp, temperature, humidity, light, distance FROM telemetry ORDER BY rowid DESC LIMIT 20")
    rows = c.fetchall()[::-1]
    conn.close()

    if not rows:
        return [go.Figure()]*4

    times = [r[0] for r in rows]
    return [
        go.Figure(data=[go.Scatter(x=times, y=[r[1] for r in rows], mode='lines+markers')], layout=go.Layout(title="Temperature (°C)")),
        go.Figure(data=[go.Scatter(x=times, y=[r[2] for r in rows], mode='lines+markers')], layout=go.Layout(title="Humidity (%)")),
        go.Figure(data=[go.Scatter(x=times, y=[r[3] for r in rows], mode='lines+markers')], layout=go.Layout(title="Light Level (ADC)")),
        go.Figure(data=[go.Scatter(x=times, y=[r[4] for r in rows], mode='lines+markers')], layout=go.Layout(title="Distance (cm)"))
    ]

if __name__ == '__main__':
    app.run_server(debug=True)