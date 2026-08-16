#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"
#include <ArduinoJson.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define LDR_PIN 34
#define TRIG_PIN 2
#define ECHO_PIN 18
#define LED_PIN 5

const char* ssid = "Nana Yaw";
const char* password = "********";
const char* mqtt_server = "broker.hivemq.com"; 
const char* data_topic = "esp32/GENES/data"; 
const char* command_topic = "esp32/GENES/control/led"; 

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);
unsigned long lastReadTime = 0;

float readDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return 0.0;
  return duration * 0.034 / 2.0;
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) message += (char)payload[i];
  message.trim();

  if (message.equalsIgnoreCase("ON")) digitalWrite(LED_PIN, HIGH);
  else if (message.equalsIgnoreCase("OFF")) digitalWrite(LED_PIN, LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  dht.begin();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    while (!client.connected()) {
      String clientId = "ESP32Group-" + String(random(0xffff), HEX);
      if (client.connect(clientId.c_str())) {
        client.subscribe(command_topic);
        break;
      }
      delay(2000);
    }
  }
  client.loop(); // Poll incoming control commands

  if (millis() - lastReadTime >= 5000) {
    lastReadTime = millis();
    StaticJsonDocument<200> doc;
    doc["temperature"] = dht.readTemperature();
    doc["humidity"] = dht.readHumidity();
    doc["light"] = analogRead(LDR_PIN);
    doc["distance"] = readDistanceCM();

    char buffer[256];
    serializeJson(doc, buffer);
    client.publish(data_topic, buffer);
  }
}