import dash
from dash import html
import paho.mqtt.client as mqtt

MQTT_BROKER = "broker.hivemq.com"
COMMAND_TOPIC = "esp32/GENES/control/led"

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Lab 6: Remote LED Actuator Control"),
    html.Button('TURN ON LED', id='btn-on', n_clicks=0, style={'padding': '15px 30px', 'backgroundColor': 'green', 'color': 'white', 'fontSize': '18px'}),
    html.Button('TURN OFF LED', id='btn-off', n_clicks=0, style={'padding': '15px 30px', 'backgroundColor': 'red', 'color': 'white', 'fontSize': '18px', 'marginLeft': '20px'}),
    html.Div(id='status-out', style={'marginTop': '20px', 'fontSize': '20px'})
])

def send_command(cmd):
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)
    client.publish(COMMAND_TOPIC, cmd)
    client.disconnect()

@app.callback(
    dash.dependencies.Output('status-out', 'children'),
    [dash.dependencies.Input('btn-on', 'n_clicks'),
     dash.dependencies.Input('btn-off', 'n_clicks')]
)
def control_led(btn_on, btn_off):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Actuator state idle."
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'btn-on':
        send_command("ON")
        return "Sent Command: TURN ON"
    elif button_id == 'btn-off':
        send_command("OFF")
        return "Sent Command: TURN OFF"

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)