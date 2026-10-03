/*
 * ESP32 Environment Monitor
 * --------------------------
 * Reads temperature & humidity from a DHT22 sensor and light level from an
 * LDR, then publishes JSON readings over MQTT (topic: esp32/env-monitor/data).
 *
 * Wiring (DHT22 -> ESP32):
 *   VCC  -> 3V3
 *   DATA -> GPIO 4
 *   GND  -> GND
 *
 * Wiring (LDR voltage divider -> ESP32):
 *   3V3 -> LDR -> GPIO 34 -> 10k resistor -> GND
 *   (GPIO 34 is an input-only ADC pin, ideal for a sensor.)
 *
 * Libraries: PubSubClient (Nick O'Leary), DHT sensor library (Adafruit),
 *            ArduinoJson (Benoit Blanchon)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ---------- CONFIG: edit these ----------
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER   = "test.mosquitto.org";   // free public broker
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "esp32/env-monitor/data";
const char* DEVICE_ID     = "esp32-01";

const unsigned long PUBLISH_INTERVAL_MS = 5000;     // publish every 5 seconds
// -----------------------------------------

#define DHTPIN   4        // GPIO pin connected to DHT22 data line
#define DHTTYPE  DHT22
#define LDRPIN   34       // ADC pin connected to the LDR divider

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastPublish = 0;

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());
}

void connectMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Connecting to MQTT broker... ");
    String clientId = DEVICE_ID + String("-") + String(random(0xffff), HEX);
    if (mqtt.connect(clientId.c_str())) {
      Serial.println("connected.");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqtt.state());
      Serial.println(" retrying in 3s");
      delay(3000);
    }
  }
}

// Map the raw ADC reading (0..4095) to a light percentage (0..100).
float readLightPercent() {
  int raw = analogRead(LDRPIN);
  float percent = (raw / 4095.0) * 100.0;
  return round(percent * 10.0) / 10.0;
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  analogReadResolution(12);   // 0..4095
  connectWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!mqtt.connected()) connectMQTT();
  mqtt.loop();

  unsigned long now = millis();
  if (now - lastPublish < PUBLISH_INTERVAL_MS) return;
  lastPublish = now;

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  float light = readLightPercent();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT22 sensor!");
    return;
  }

  StaticJsonDocument<160> doc;
  doc["device"] = DEVICE_ID;
  doc["temperature"] = round(temperature * 10.0) / 10.0;
  doc["humidity"] = round(humidity * 10.0) / 10.0;
  doc["light"] = light;

  char payload[160];
  serializeJson(doc, payload);

  if (mqtt.publish(MQTT_TOPIC, payload)) {
    Serial.print("Published: ");
    Serial.println(payload);
  } else {
    Serial.println("Publish failed (payload too large or not connected)");
  }
}
