# telemetry_subscriber.py

import json
import threading
import time
import requests
from websocket import WebSocketApp

# ----- CẤU HÌNH ThingsBoard -----
TB_HOST = 'app.coreiot.io'
TB_REST_PORT = 80
TB_WS_PORT = 80

TENANT_USER = 'minh.pham2212075@hcmut.edu.vn'    # Your email
TENANT_PASS = '2212075'    # Your password
DEVICE_ID = 'eb308820-ed8e-11ef-87b5-21bccf7d29d5'
JWT_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJtaW5oLnBoYW0yMjEyMDc1QGhjbXV0LmVkdS52biIsInVzZXJJZCI6IjY0ZWNiYzcwLWVkOGUtMTFlZi04N2I1LTIxYmNjZjdkMjlkNSIsInNjb3BlcyI6WyJURU5BTlRfQURNSU4iXSwic2Vzc2lvbklkIjoiYTMwODg5NTAtMzVhYy00OGYzLTg4NDAtOTVmZjZhMmNhMzJhIiwiZXhwIjoxNzQ5MDIzNDc0LCJpc3MiOiJjb3JlaW90LmlvIiwiaWF0IjoxNzQ5MDE0NDc0LCJmaXJzdE5hbWUiOiJNSU5IIiwibGFzdE5hbWUiOiJQSOG6oE0gUVVBTkciLCJlbmFibGVkIjp0cnVlLCJpc1B1YmxpYyI6ZmFsc2UsInRlbmFudElkIjoiNjRlMzZkYTAtZWQ4ZS0xMWVmLTg3YjUtMjFiY2NmN2QyOWQ1IiwiY3VzdG9tZXJJZCI6IjEzODE0MDAwLTFkZDItMTFiMi04MDgwLTgwODA4MDgwODA4MCJ9.6X5LjKZoxwvJXr6VUrHe3ONWqo2KMwoohHeOFbWce_nG1d-sXOF1DxYYolhQ27pbbMmguYYj83KAQHRI5Q-GXA"


class TelemetrySubscriber:
    def __init__(self, host = TB_HOST, rest_port = TB_REST_PORT, ws_port = TB_WS_PORT, username = TENANT_USER, password = TENANT_PASS, device_id = DEVICE_ID):
        self.host = host
        self.rest_port = rest_port
        self.ws_port = ws_port
        self.username = username
        self.password = password
        self.device_id = device_id
        self.token = None
        self.ws_app = None
        self.telemetry_data = {}  # Lưu trữ dữ liệu telemetry mới nhất
        self.connected = False

    def get_jwt_token(self):
        return JWT_TOKEN  # Trả về JWT token đã được cấu hình sẵn

    def on_message(self, ws, message):
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            print("❗ Không parse được message JSON:", message)
            return

        if 'subscriptionId' in payload and 'data' in payload:
            data = payload['data']
            for key, values in data.items():
                if isinstance(values, list) and len(values) > 0:
                    _, value = values[0]
                    self.telemetry_data[key] = value  # Lưu giá trị mới nhất
        elif 'subscriptionId' in payload and payload.get('errorCode') == 0:
            print(f"✅ Đã kết nối telemetry subscription ID: {payload['subscriptionId']}")
            self.connected = True
        else:
            print("ℹ️ Message khác:", payload)

    def on_error(self, ws, error):
        print("🚨 WebSocket error:", error)

    def on_close(self, ws, code, reason):
        print(f"🔒 WebSocket đóng (code={code}, reason={reason})")
        self.connected = False

    def on_open(self, ws):
        print("🔌 WebSocket kết nối thành công.")
        subscribe_payload = {
            "tsSubCmds": [
                {
                    "entityType": "DEVICE",
                    "entityId": self.device_id,
                    "scope": "LATEST_TELEMETRY",
                    "cmdId": 1
                }
            ]
        }
        ws.send(json.dumps(subscribe_payload))

    def start(self):
        if not self.token:
            self.get_jwt_token()
            
        ws_url = f"ws://{self.host}:{self.ws_port}/api/ws/plugins/telemetry?token={self.token}"

        self.ws_app = WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        thread = threading.Thread(target=self.ws_app.run_forever, kwargs={'ping_interval': 20, 'ping_timeout': 10})
        thread.daemon = True
        thread.start()

    def get_telemetry_value(self, key: str):
        return self.telemetry_data.get(key)

    def get_all_telemetry(self):
        return dict(self.telemetry_data)


# Nếu file này được chạy trực tiếp, test nhanh kết nối
if __name__ == "__main__":
    subscriber = TelemetrySubscriber(
        TB_HOST, TB_REST_PORT, TB_WS_PORT,
        TENANT_USER, TENANT_PASS, DEVICE_ID
    )
    subscriber.start()
    print("⏳ Đang lắng nghe dữ liệu telemetry... Nhấn Ctrl+C để dừng.")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Dừng chương trình.")
