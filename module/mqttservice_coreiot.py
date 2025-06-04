#   module/mqttservice_coreiot.py
import paho.mqtt.client as mqtt
import requests

# === Cấu hình ThingsBoard Cloud ===
THINGSBOARD_HOST = "app.coreiot.io"
THINGSBOARD_PORT = 1883
ACCESS_TOKEN = "aInZbDDLhqg9PaTWZUYr"  # Thay bằng access token của thiết bị trên ThingsBoard
JWT_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ2dS5uZ3V5ZW5jb25nQGhjbXV0LmVkdS52biIsInVzZXJJZCI6IjQ1ZTkzYzcwLWUxZGQtMTFlZi1hZDA5LTUxNWY3OTBlZDlkZiIsInNjb3BlcyI6WyJURU5BTlRfQURNSU4iXSwic2Vzc2lvbklkIjoiN2VmZDM3MGYtYTRkZi00Yjk3LWEwYzQtZGJiM2NhZGU5YmQzIiwiZXhwIjoxNzQ3MDQ4MDYyLCJpc3MiOiJjb3JlaW90LmlvIiwiaWF0IjoxNzQ3MDM5MDYyLCJmaXJzdE5hbWUiOiJWxakiLCJsYXN0TmFtZSI6Ik5ndXnhu4VuIEPDtG5nIiwiZW5hYmxlZCI6dHJ1ZSwiaXNQdWJsaWMiOmZhbHNlLCJ0ZW5hbnRJZCI6IjQ1ZTE3NDQwLWUxZGQtMTFlZi1hZDA5LTUxNWY3OTBlZDlkZiIsImN1c3RvbWVySWQiOiIxMzgxNDAwMC0xZGQyLTExYjItODA4MC04MDgwODA4MDgwODAifQ.YzasnOFtU86GEIgFcfcXy3FcozQ6AEt_mXCKCkqjMKQU-Ydn6lW8-tFTVhpEvSPIoIv_5y04XC251Wsaz-aQnw"
DEVICE_ID = "ff1ebc00-e693-11ef-87b5-21bccf7d29d5"  # Thay bằng deviceId của thiết bị trên ThingsBoard
# === MQTT client setup ===
client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Đã kết nối tới ThingsBoard Cloud MQTT Broker")
    else:
        print(f"Kết nối lỗi, mã trả về: {rc}")

client.on_connect = on_connect

client.connect(THINGSBOARD_HOST, THINGSBOARD_PORT)
client.loop_start()

def publish_telemetry(payload: dict):
    """
    Gửi dữ liệu telemetry lên ThingsBoard.
    payload: dict, ví dụ {"temperature": 25}
    """
    import json
    topic = "v1/devices/me/telemetry"
    result = client.publish(topic, json.dumps(payload))
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        print('Lỗi gửi MQTT:', mqtt.error_string(result.rc))
    else:
        print(f'Đã gửi telemetry: {payload}')

def publish_attribute(payload: dict):
    """
    Gửi thuộc tính (attributes) lên ThingsBoard.
    """
    import json
    topic = "v1/devices/me/attributes"
    result = client.publish(topic, json.dumps(payload))
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        print('Lỗi gửi MQTT:', mqtt.error_string(result.rc))
    else:
        print(f'Đã gửi attribute: {payload}')

def request_attribute(type: str, key: str):
    """
    Gửi yêu cầu lấy thuộc tính có tên key và loại là type (client, shared) từ ThingsBoard.
    """
    url = f"https://{THINGSBOARD_HOST}/api/v1/{ACCESS_TOKEN}/attributes"
    params = {}
    if type == "client":
        params["clientKeys"] = key
    elif type == "shared":
        params["sharedKeys"] = key
    else:
        print("Loại attribute không hợp lệ. Chỉ hỗ trợ 'client' hoặc 'shared'.")
        return None
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # Trả về giá trị attribute nếu có
        if type == "client" and "client" in data and key in data["client"]:
            return data["client"][key]
        elif type == "shared" and "shared" in data and key in data["shared"]:
            return data["shared"][key]
        else:
            print(f"Không tìm thấy attribute '{key}' loại '{type}'")
            return None
    except Exception as e:
        print(f"Lỗi lấy attribute '{key}' loại '{type}': {e}")
        return None

def get_latest_telemetry(key: str, jwt_token: str, device_id: str):
    """
    Lấy giá trị telemetry mới nhất qua REST API (cần JWT token và deviceId).
    """
    url = f"https://{THINGSBOARD_HOST}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys={key}"
    headers = {
        "X-Authorization": f"{jwt_token}"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # Dữ liệu trả về dạng: {"temperature": [{"ts":..., "value":...}], ...}
        if key in data and isinstance(data[key], list) and data[key]:
            return data[key][0].get("value")
        else:
            print(f"Không tìm thấy telemetry '{key}'")
            return None
    except Exception as e:
        print(f"Lỗi lấy dữ liệu telemetry '{key}': {e}")
        return None

def get_temperature():
    """
    Lấy giá trị temperature telemetry mới nhất.
    """
    return get_latest_telemetry("temperature", JWT_TOKEN, DEVICE_ID)

def get_humidity():
    """
    Lấy giá trị humidity telemetry mới nhất.
    """
    return get_latest_telemetry("humidity", JWT_TOKEN, DEVICE_ID)

def get_energy_consumption():
    """
    Lấy giá trị energy telemetry mới nhất.
    """
    return get_latest_telemetry("energy", JWT_TOKEN, DEVICE_ID)
def get_brightness():
    """
    Lấy giá trị brightness telemetry mới nhất.
    """
    return get_latest_telemetry("brightness", JWT_TOKEN, DEVICE_ID)

def turn_on_fan():
    """
    Bật quạt (gửi '1' tới feed Fan)
    """
    publish_attribute({"fan": True})

def turn_off_fan():
    """
    Tắt quạt (gửi '0' tới feed Fan)
    """
    publish_attribute({"fan": False})

def turn_on_light():
    """
    Bật đèn (gửi '1' tới feed Light)
    """
    publish_attribute({"light": True})


def turn_off_light():
    """
    Tắt đèn (gửi '0' tới feed Light)
    """
    publish_attribute({"light": False})

def status_fan():
    """
    Lấy trạng thái quạt (True/False)
    """
    return request_attribute("shared", "fan")

def status_light():
    """
    Lấy trạng thái đèn (True/False)
    """
    return request_attribute("shared", "light")

def get_chat():
    """
    Lấy giá trị chuỗi 
    """
# Nếu chạy trực tiếp
if __name__ == "__main__":
    import time
    publish_telemetry({"temperature": 30})
    publish_telemetry({"humidity": 60})
    print("Giá trị nhiệt độ mới nhất:", get_temperature())
    print("Giá trị độ ẩm mới nhất:", get_humidity())
    time.sleep(1)
    client.loop_stop()
    client.disconnect()
