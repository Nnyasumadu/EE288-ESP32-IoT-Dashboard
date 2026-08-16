#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"
#include <ArduinoJson.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define LDR_PIN 34
#define TRIG_PIN 2
#define ECHO_PIN 18

const char* ssid = "Nana Yaw";
const char* password = "********";
const char* mqtt_server = "broker.hivemq.com"; 
const char* data_topic = "esp32/GENES/data"; 

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

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

void reconnectMQTT() {
  while (!client.connected()) {
    String clientId = "ESP32Group-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) break;
    delay(2000);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  dht.begin();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) reconnectMQTT();
  client.loop();

  StaticJsonDocument<200> doc;
  doc["temperature"] = dht.readTemperature();
  doc["humidity"] = dht.readHumidity();
  doc["light"] = analogRead(LDR_PIN);
  doc["distance"] = readDistanceCM();

  char buffer[256];
  serializeJson(doc, buffer);
  client.publish(data_topic, buffer);

  delay(5000);
}