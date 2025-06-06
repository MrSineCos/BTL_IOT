#include <WiFi.h>
#include <Arduino_MQTT_Client.h>
#include <OTA_Firmware_Update.h>
#include <ThingsBoard.h>
#include <Shared_Attribute_Update.h>
#include <Attribute_Request.h>
#include <Espressif_Updater.h>
#include <DHT20.h>

// ========================= THIẾT LẬP WIFI & THINGSBOARD =========================
constexpr char WIFI_SSID[] = "Bonjour";
constexpr char WIFI_PASSWORD[] = "hellosine";
constexpr char TOKEN[] = "l4y3xa2qhekvg7rng4x5";
constexpr char THINGSBOARD_SERVER[] = "app.coreiot.io";
constexpr uint16_t THINGSBOARD_PORT = 1883U;

// ========================= THIẾT LẬP FIRMWARE OTA =========================
constexpr char CURRENT_FIRMWARE_TITLE[] = "OTA_DHT20";
constexpr char CURRENT_FIRMWARE_VERSION[] = "1.0";
constexpr uint8_t FIRMWARE_FAILURE_RETRIES = 12U;   // Số lần thử lại khi OTA thất bại
constexpr uint16_t FIRMWARE_PACKET_SIZE = 4096U;    // Kích thước gói tin OTA
constexpr uint16_t MAX_MESSAGE_SEND_SIZE = 512U;    // Kích thước tối đa tin nhắn gửi
constexpr uint16_t MAX_MESSAGE_RECEIVE_SIZE = 512U; // Kích thước tối đa tin nhắn nhận

// ========================= THIẾT LẬP CHÂN CẢM BIẾN =========================
constexpr int GP2Y_LED_PIN = 5; // Chân LED của cảm biến bụi GP2Y1010
constexpr int GP2Y_VO_PIN = 2;  // Chân analog đọc giá trị cảm biến bụi

// ========================= KHÓA TELEMETRY CHO THINGSBOARD =========================
constexpr char TEMPERATURE_KEY[] = "temperature";
constexpr char HUMIDITY_KEY[] = "humidity";
constexpr char MQ2_KEY[] = "mq2";
constexpr char DUST_KEY[] = "dust";

// ========================= KHỞI TẠO CÁC ĐỐI TƯỢNG =========================
DHT20 dht20;                               // Cảm biến nhiệt độ, độ ẩm DHT20
WiFiClient espClient;                      // Client WiFi
Arduino_MQTT_Client mqttClient(espClient); // Client MQTT

// Các callback objects cho ThingsBoard
Shared_Attribute_Update<1U, 2U> shared_update; // Cập nhật thuộc tính chia sẻ
Attribute_Request<2U, 2U> attr_request;        // Yêu cầu thuộc tính
Espressif_Updater<> updater;                   // Cập nhật firmware cho ESP32
OTA_Firmware_Update<> ota;                     // Cập nhật OTA

// Khởi tạo ThingsBoard với các APIs
const std::array<IAPI_Implementation *, 3U> apis = {&shared_update, &attr_request, &ota};
ThingsBoard tb(mqttClient, MAX_MESSAGE_RECEIVE_SIZE, MAX_MESSAGE_SEND_SIZE, Default_Max_Stack_Size, apis);

// ========================= CÁC BIẾN TRẠNG THÁI =========================
bool tbConnected = false;    // Trạng thái kết nối ThingsBoard
bool otaInitialized = false; // Trạng thái khởi tạo OTA
bool isOTAUpdating = false;  // Trạng thái đang cập nhật OTA

// ========================= HANDLES CỦA CÁC TASK =========================
TaskHandle_t Telemetry_Task_Handle = NULL;
TaskHandle_t Sensor_Task_Handle = NULL;
TaskHandle_t OTA_Task_Handle = NULL;

// ========================= DỮ LIỆU CẢM BIẾN =========================
float temperature, humidity, dustDensity; // Nhiệt độ, độ ẩm, nồng độ bụi
int mq2Value;                             // Giá trị cảm biến khí gas MQ2

// ========================= KHAI BÁO HÀM =========================
void WiFiTask(void *pvParameters);
void SensorTask(void *pvParameters);
void TelemetryTask(void *pvParameters);
void OTATask(void *pvParameters);
float readGP2Y1010();

void setup()
{
  Serial.begin(115200);
  Serial.println("Khởi động ESP32...");

  // Thiết lập chân cho cảm biến bụi GP2Y1010
  pinMode(GP2Y_LED_PIN, OUTPUT);
  digitalWrite(GP2Y_LED_PIN, HIGH); // Tắt LED cảm biến bụi

  // Tạo các task với mức độ ưu tiên khác nhau
  xTaskCreate(WiFiTask, "WiFiTask", 8192, NULL, 2, NULL);                             // Task WiFi - Ưu tiên cao nhất
  xTaskCreate(SensorTask, "SensorTask", 4096, NULL, 1, &Sensor_Task_Handle);          // Task đọc cảm biến
  xTaskCreate(TelemetryTask, "TelemetryTask", 8192, NULL, 1, &Telemetry_Task_Handle); // Task gửi dữ liệu
  xTaskCreate(OTATask, "OTATask", 8192, NULL, 1, &OTA_Task_Handle);                   // Task cập nhật OTA

  Serial.println("Đã tạo tất cả các task");
}

void loop()
{
  // FreeRTOS - không sử dụng loop()
  vTaskDelay(1000 / portTICK_PERIOD_MS);
}

// ========================= TASK QUẢN LÝ WIFI & THINGSBOARD =========================
void WiFiTask(void *pvParameters)
{
  while (true)
  {
    // Kiểm tra kết nối WiFi
    if (WiFi.status() != WL_CONNECTED)
    {
      Serial.println("Đang kết nối WiFi...");
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

      int attempts = 0;
      while (WiFi.status() != WL_CONNECTED && attempts < 20)
      {
        vTaskDelay(500 / portTICK_PERIOD_MS);
        Serial.print(".");
        attempts++;
      }

      if (WiFi.status() == WL_CONNECTED)
      {
        Serial.println("\nKết nối WiFi thành công");
        Serial.printf("Địa chỉ IP: %s\n", WiFi.localIP().toString().c_str());
      }
      else
      {
        Serial.println("\nKết nối WiFi thất bại!");
        vTaskDelay(5000 / portTICK_PERIOD_MS);
        continue;
      }
    }

    // Kiểm tra kết nối ThingsBoard
    if (WiFi.status() == WL_CONNECTED && !tb.connected())
    {
      Serial.println("Đang kết nối tới ThingsBoard...");
      if (tb.connect(THINGSBOARD_SERVER, TOKEN, THINGSBOARD_PORT))
      {
        Serial.println("Kết nối ThingsBoard thành công");
        tbConnected = true;
        otaInitialized = false; // Reset cờ OTA khi kết nối lại
      }
      else
      {
        Serial.println("Kết nối ThingsBoard thất bại");
        tbConnected = false;
      }
    }

    vTaskDelay(5000 / portTICK_PERIOD_MS); // Kiểm tra mỗi 5 giây
  }
}

// ========================= TASK ĐỌC DỮ LIỆU CẢM BIẾN =========================
void SensorTask(void *pvParameters)
{
  while (true)
  {
    // Đọc giá trị cảm biến DHT20
    if (dht20.read() == DHT20_OK)
    {
      temperature = dht20.getTemperature();
      humidity = dht20.getHumidity();
    }
    // temperature = 27.0;  // Giá trị mặc định nhiệt độ
    // humidity = 50.0;     // Giá trị mặc định độ ẩm

    // Đọc giá trị cảm biến khí gas MQ2
    mq2Value = analogRead(1);

    // Đọc giá trị cảm biến bụi GP2Y1010
    dustDensity = readGP2Y1010();

    // In thông tin debug ra Serial Monitor
    Serial.printf("[CẢM BIẾN] Nhiệt độ: %.1f°C, Độ ẩm: %.1f%%, MQ2: %d, Bụi: %.3f mg/m³\n",
                  temperature, humidity, mq2Value, dustDensity);

    vTaskDelay(2000 / portTICK_PERIOD_MS); // Đọc cảm biến mỗi 2 giây
  }
}

// ========================= TASK GỬI DỮ LIỆU TELEMETRY =========================
void TelemetryTask(void *pvParameters)
{
  while (true)
  {
    // Chỉ gửi dữ liệu khi kết nối thành công và không đang cập nhật OTA
    if (tbConnected && tb.connected() && !isOTAUpdating)
    {
      Serial.printf("[TELEMETRY] Đang gửi - Nhiệt độ: %.1f, Độ ẩm: %.1f, MQ2: %d, Bụi: %.3f\n",
                    temperature, humidity, mq2Value, dustDensity);

      // Gửi dữ liệu telemetry lên ThingsBoard
      bool success = true;
      success &= tb.sendTelemetryData(TEMPERATURE_KEY, temperature);
      success &= tb.sendTelemetryData(HUMIDITY_KEY, humidity);
      success &= tb.sendTelemetryData(MQ2_KEY, mq2Value);
      success &= tb.sendTelemetryData(DUST_KEY, dustDensity);

      if (!success)
      {
        Serial.println("[TELEMETRY] Gửi dữ liệu thất bại!");
      }
    }

    // Xử lý tin nhắn từ ThingsBoard
    tb.loop();
    vTaskDelay(5000 / portTICK_PERIOD_MS); // Gửi dữ liệu mỗi 5 giây
  }
}

// ========================= TASK QUẢN LÝ CẬP NHẬT OTA =========================
void OTATask(void *pvParameters)
{
  bool updateRequestSent = false;
  while (true)
  {
    if (tb.connected() && !isOTAUpdating)
    {
      Serial.println("[OTA] Đang khởi tạo cập nhật OTA...");

      // Gửi thông tin firmware hiện tại
      if (ota.Firmware_Send_Info(CURRENT_FIRMWARE_TITLE, CURRENT_FIRMWARE_VERSION))
      {
        Serial.println("[OTA] Gửi thông tin firmware thành công");
      }
      else
      {
        Serial.println("[OTA] Gửi thông tin firmware thất bại");
      }

      if (!updateRequestSent)
      {
        // Tạo callback cho quá trình cập nhật OTA
        OTA_Update_Callback callback(
            CURRENT_FIRMWARE_TITLE,
            CURRENT_FIRMWARE_VERSION,
            &updater,
            // Callback khi cập nhật hoàn tất
            [](const bool &success)
            {
              if (success)
              {
                Serial.println("[OTA] Cập nhật thành công! Đang khởi động lại...");
                vTaskDelay(1000 / portTICK_PERIOD_MS);
                esp_restart();
              }
              else
              {
                vTaskResume(Sensor_Task_Handle);
                isOTAUpdating = false;
                Serial.println("[OTA] Cập nhật thất bại!");
              }
            },
            // Callback hiển thị tiến trình cập nhật
            [](const size_t &current, const size_t &total)
            {
              float progress = (float)current * 100.0 / total;
              Serial.printf("[OTA] Tiến trình: %.2f%% (%zu/%zu bytes)\n", progress, current, total);
            },
            // Callback khi bắt đầu cập nhật
            []()
            {
              isOTAUpdating = true;
              vTaskSuspend(Sensor_Task_Handle); // Tạm dừng task cảm biến
                                                // Chỉ dừng Sensory_Task, không dừng Telemetry_Task vì sẽ dừng tài nguyên Thingsboard tb theo khiến OTA_Task không chạy được

              Serial.println("[OTA] Bắt đầu cập nhật...");
            },
            FIRMWARE_FAILURE_RETRIES,
            FIRMWARE_PACKET_SIZE);

        Serial.print(CURRENT_FIRMWARE_TITLE);
        Serial.println(CURRENT_FIRMWARE_VERSION);
        Serial.println("Đang cập nhật Firmware...");

        // Bắt đầu quá trình cập nhật firmware
        updateRequestSent = ota.Start_Firmware_Update(callback);
        if (updateRequestSent)
        {
          Serial.println("Đăng ký nhận cập nhật Firmware...");
          updateRequestSent = ota.Subscribe_Firmware_Update(callback);
        }
      }
    }

    // Xử lý tin nhắn từ ThingsBoard
    tb.loop();
    vTaskDelay(30000 / portTICK_PERIOD_MS); // Kiểm tra OTA mỗi 30 giây
  }
}

// ========================= HÀM ĐỌC CẢM BIẾN BỤI GP2Y1010 =========================
float readGP2Y1010()
{
  // Bật LED cảm biến (LOW = bật vì LED cathode chung)
  digitalWrite(GP2Y_LED_PIN, LOW);
  delayMicroseconds(280); // Chờ 0.28ms để LED ổn định

  // Đọc giá trị analog từ cảm biến
  int voRaw = analogRead(GP2Y_VO_PIN);

  // Tắt LED cảm biến
  digitalWrite(GP2Y_LED_PIN, HIGH);
  delayMicroseconds(9680); // Chờ 9.68ms để hoàn thành chu kỳ 10ms

  // Chuyển đổi giá trị ADC sang điện áp (ESP32: 12-bit ADC, 3.3V)
  float voltage = voRaw * (3.3 / 4095.0);

  // Chuyển đổi điện áp sang nồng độ bụi (mg/m³) theo datasheet GP2Y1010
  float dust = 0.17 * voltage - 0.1;

  return dust < 0 ? 0.0 : dust; // Trả về 0 nếu giá trị âm
}