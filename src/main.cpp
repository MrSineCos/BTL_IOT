#include <WiFi.h>
#include <Arduino_MQTT_Client.h>
#include <OTA_Firmware_Update.h>
#include <ThingsBoard.h>
#include <Shared_Attribute_Update.h>
#include <Attribute_Request.h>
#include <Espressif_Updater.h>
#include <DHT20.h>

// WiFi & ThingsBoard Config
constexpr char WIFI_SSID[] = "ACLAB";
constexpr char WIFI_PASSWORD[] = "ACLAB2023";
constexpr char TOKEN[] = "X19l788unSsVNz5D6HTW";
constexpr char THINGSBOARD_SERVER[] = "app.coreiot.io";
constexpr uint16_t THINGSBOARD_PORT = 1883U;

constexpr char CURRENT_FIRMWARE_TITLE[] = "OTA_DHT20";
constexpr char CURRENT_FIRMWARE_VERSION[] = "1.0";

// Sensor config
constexpr int GP2Y_LED_PIN = 5;
constexpr int GP2Y_VO_PIN = 2;

// ThingsBoard Keys
constexpr char TEMPERATURE_KEY[] = "temperature";
constexpr char HUMIDITY_KEY[] = "humidity";
constexpr char MQ2_KEY[] = "mq2";
constexpr char DUST_KEY[] = "dust";

// DHT20 and TB object
DHT20 dht20;
WiFiClient espClient;
Arduino_MQTT_Client mqttClient(espClient);
ThingsBoard tb(mqttClient);
Espressif_Updater<> updater;
OTA_Firmware_Update<> ota;
Shared_Attribute_Update<1U, 2U> shared_update;
Attribute_Request<2U, 2U> attr_request;
const std::array<IAPI_Implementation*, 3U> apis = { &shared_update, &attr_request, &ota };

// Flags
bool tbConnected = false;

// Sensor data
float temperature, humidity, dustDensity;
int mq2Value;

// Forward declarations
void WiFiTask(void *pvParameters);
void SensorTask(void *pvParameters);
void TelemetryTask(void *pvParameters);
void OTATask(void *pvParameters);
float readGP2Y1010();

void setup() {
  Serial.begin(115200);
  Wire.begin(11, 12);
  dht20.begin();

  pinMode(GP2Y_LED_PIN, OUTPUT);
  digitalWrite(GP2Y_LED_PIN, HIGH); // Turn off dust LED

  xTaskCreatePinnedToCore(WiFiTask, "WiFiTask", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(SensorTask, "SensorTask", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(TelemetryTask, "TelemetryTask", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(OTATask, "OTATask", 4096, NULL, 1, NULL, 1);
}

void loop() {
  // FreeRTOS nên không dùng gì trong loop()
}

// ========================= WiFi Task =========================
void WiFiTask(void *pvParameters) {
  while (true) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("Connecting to WiFi...");
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      while (WiFi.status() != WL_CONNECTED) {
        vTaskDelay(500 / portTICK_PERIOD_MS);
        Serial.print(".");
      }
      Serial.println("\nWiFi connected");
    }

    if (!tb.connected()) {
      Serial.println("Connecting to ThingsBoard...");
      if (tb.connect(THINGSBOARD_SERVER, TOKEN, THINGSBOARD_PORT)) {
        Serial.println("Connected to ThingsBoard");
        tbConnected = true;
      } else {
        Serial.println("TB connect failed.");
        tbConnected = false;
      }
    }

    tb.loop();
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}

// ========================= Sensor Task =========================
void SensorTask(void *pvParameters) {
  while (true) {
    dht20.read();
    temperature = dht20.getTemperature();
    humidity = dht20.getHumidity();
    mq2Value = analogRead(1);
    dustDensity = readGP2Y1010();

    vTaskDelay(2000 / portTICK_PERIOD_MS);
  }
}

// ========================= Telemetry Task =========================
void TelemetryTask(void *pvParameters) {
  while (true) {
    if (tbConnected) {
      Serial.printf("[TELEMETRY] Temp: %.1f, Hum: %.1f, MQ2: %d, Dust: %.3f\n", temperature, humidity, mq2Value, dustDensity);
      tb.sendTelemetryData(TEMPERATURE_KEY, temperature);
      tb.sendTelemetryData(HUMIDITY_KEY, humidity);
      tb.sendTelemetryData(MQ2_KEY, mq2Value);
      tb.sendTelemetryData(DUST_KEY, dustDensity);
    }
    vTaskDelay(5000 / portTICK_PERIOD_MS);  // Send every 5s
  }
}

// ========================= OTA Task =========================
void OTATask(void *pvParameters) {
  bool sent = false;
  while (true) {
    if (tbConnected && !sent) {
      ota.Firmware_Send_Info(CURRENT_FIRMWARE_TITLE, CURRENT_FIRMWARE_VERSION);

      OTA_Update_Callback callback(
        CURRENT_FIRMWARE_TITLE,
        CURRENT_FIRMWARE_VERSION,
        &updater,
        [](const bool &success) {
          if (success) {
            Serial.println("Update successful! Restarting...");
            esp_restart();
          } else {
            Serial.println("OTA failed.");
          }
        },
        [](const size_t &current, const size_t &total) {
          Serial.printf("Progress: %.2f%%\n", (float)current * 100 / total);
        },
        []() {
          Serial.println("OTA update started...");
        }
      );

      ota.Start_Firmware_Update(callback);
      ota.Subscribe_Firmware_Update(callback);

      sent = true;
    }

    vTaskDelay(10000 / portTICK_PERIOD_MS);
  }
}

// ========================= GP2Y1010 Dust Sensor =========================
float readGP2Y1010() {
  digitalWrite(GP2Y_LED_PIN, LOW);
  delayMicroseconds(280);
  int voRaw = analogRead(GP2Y_VO_PIN);
  digitalWrite(GP2Y_LED_PIN, HIGH);
  delayMicroseconds(9680);

  float voltage = voRaw * (3.3 / 4095.0);
  float dust = 0.17 * voltage - 0.1;
  return dust < 0 ? 0.0 : dust;
}
