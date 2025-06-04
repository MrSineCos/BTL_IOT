# websocketAPI/telemetry_subscriber.py

import json
import threading
import time
import requests
from websocket import WebSocketApp

# ----- CẤU HÌNH ThingsBoard -----
TB_HOST = 'app.coreiot.io'
TB_REST_PORT = 80
TB_WS_PORT = 80

TENANT_USER = 'sinecoswifi@gmail.com'    # Your email
TENANT_PASS = '123sc123'    # Your password
DEVICE_ID = 'b25a5f30-2a51-11f0-a3c9-ab0d8999f561'


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
        login_url = f"http://{self.host}:{self.rest_port}/api/auth/login"
        payload = {
            "username": self.username,
            "password": self.password
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        resp = requests.post(login_url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        token = data.get('token')
        if not token:
            raise RuntimeError("Không lấy được token từ ThingsBoard.")
        self.token = token
        return token

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
