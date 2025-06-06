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
JWT_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJtaW5oLnBoYW0yMjEyMDc1QGhjbXV0LmVkdS52biIsInVzZXJJZCI6IjY0ZWNiYzcwLWVkOGUtMTFlZi04N2I1LTIxYmNjZjdkMjlkNSIsInNjb3BlcyI6WyJURU5BTlRfQURNSU4iXSwic2Vzc2lvbklkIjoiMDQ3MzUyMTMtMDU5NC00M2JlLTk0ZGUtYTlhYzMwODJkYmZhIiwiZXhwIjoxNzQ5MDMzNzM5LCJpc3MiOiJjb3JlaW90LmlvIiwiaWF0IjoxNzQ5MDI0NzM5LCJmaXJzdE5hbWUiOiJNSU5IIiwibGFzdE5hbWUiOiJQSOG6oE0gUVVBTkciLCJlbmFibGVkIjp0cnVlLCJpc1B1YmxpYyI6ZmFsc2UsInRlbmFudElkIjoiNjRlMzZkYTAtZWQ4ZS0xMWVmLTg3YjUtMjFiY2NmN2QyOWQ1IiwiY3VzdG9tZXJJZCI6IjEzODE0MDAwLTFkZDItMTFiMi04MDgwLTgwODA4MDgwODA4MCJ9.aTTCJSXB_aUf8PiWS2TkvWwrGZXOcunWgFWM3Z2gvpt_JbSHr45Ot4auNuJOgQMupg7Ko7QhnXabVLXESUnOxQ"


class TelemetrySubscriber:
    def __init__(self, host = TB_HOST, rest_port = TB_REST_PORT, ws_port = TB_WS_PORT, username = TENANT_USER, password = TENANT_PASS, device_id = DEVICE_ID):
        """
        Khởi tạo TelemetrySubscriber để kết nối với ThingsBoard
        
        Args:
            host (str): Địa chỉ ThingsBoard server
            rest_port (int): Port cho REST API
            ws_port (int): Port cho WebSocket
            username (str): Email đăng nhập ThingsBoard
            password (str): Mật khẩu đăng nhập ThingsBoard
            device_id (str): ID của device trên ThingsBoard
        """
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
        self.device_token = None  # Token cho device để push telemetry

    def get_jwt_token(self):
        """
        Lấy JWT token để authenticate với ThingsBoard API
        
        Returns:
            str: JWT token để sử dụng cho các API calls
            Add commentMore actions
        Raises:
            RuntimeError: Khi không thể lấy được token từ ThingsBoard
        """
        return JWT_TOKEN  # Trả về JWT token đã được cấu hình sẵn
    
    def get_device_token(self):
        """
        Lấy device access token để push telemetry data lên ThingsBoard
        
        Returns:
            str: Device access token để push telemetry
            None: Nếu không thể lấy được token
            
        Note:
            Cần JWT token trước khi gọi method này
        """
        if not self.token:
            self.get_jwt_token()
            
        device_url = f"http://{self.host}:{self.rest_port}/api/device/{self.device_id}/credentials"
        headers = {
            "X-Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

        try:
            resp = requests.get(device_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            device_token = data.get('credentialsId')
            if not device_token:
                raise RuntimeError("Không lấy được device token từ ThingsBoard.")
            self.device_token = device_token
            return device_token
        except Exception as e:
            print(f"❗ Lỗi khi lấy device token: {e}")
            return None

    def isConnect(self) ->bool:
        """
        Checks if the connection to the telemetry service is currently established.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.connected

    def push_telemetry(self, telemetry_data: dict):
        """
        Push telemetry data lên ThingsBoard qua REST API
        
        Args:
            telemetry_data (dict): Dictionary chứa dữ liệu telemetry
                                 Ví dụ: {"temperature": 25.5, "humidity": 60}
        
        Returns:
            bool: True nếu push thành công, False nếu thất bại
            
        Example:
            >>> subscriber.push_telemetry({"temperature": 25.5, "humidity": 60})
            True
        """
        if not self.device_token:
            if not self.get_device_token():
                print("❗ Không thể lấy device token để push telemetry")
                return False

        telemetry_url = f"http://{self.host}:{self.rest_port}/api/v1/{self.device_token}/telemetry"
        headers = {
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(telemetry_url, json=telemetry_data, headers=headers, timeout=10)
            resp.raise_for_status()
            print(f"✅ Push telemetry thành công: {telemetry_data}")
            return True
        except Exception as e:
            print(f"❗ Lỗi khi push telemetry: {e}")
            return False

    def push_telemetry_with_timestamp(self, telemetry_data: dict, timestamp: int = None):
        """
        Push telemetry data với timestamp cụ thể lên ThingsBoard
        
        Args:
            telemetry_data (dict): Dictionary chứa dữ liệu telemetry
                                 Ví dụ: {"temperature": 25.5, "humidity": 60}
            timestamp (int, optional): Unix timestamp tính bằng milliseconds
                                     Nếu None sẽ sử dụng thời gian hiện tại
        
        Returns:
            bool: True nếu push thành công, False nếu thất bại
            
        Example:
            >>> timestamp = int(time.time() * 1000)
            >>> subscriber.push_telemetry_with_timestamp({"temp": 25.5}, timestamp)
            True
        """
        if not self.device_token:
            if not self.get_device_token():
                print("❗ Không thể lấy device token để push telemetry")
                return False

        if timestamp is None:
            timestamp = int(time.time() * 1000)

        # Format dữ liệu với timestamp
        formatted_data = {
            "ts": timestamp,
            "values": telemetry_data
        }

        telemetry_url = f"http://{self.host}:{self.rest_port}/api/v1/{self.device_token}/telemetry"
        headers = {
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(telemetry_url, json=formatted_data, headers=headers, timeout=10)
            resp.raise_for_status()
            print(f"✅ Push telemetry với timestamp thành công: {formatted_data}")
            return True
        except Exception as e:
            print(f"❗ Lỗi khi push telemetry với timestamp: {e}")
            return False

    def push_multiple_telemetry(self, telemetry_list: list):
        """
        Push nhiều bản ghi telemetry cùng lúc lên ThingsBoard
        
        Args:
            telemetry_list (list): Danh sách các dictionary telemetry với timestamp
                                 Ví dụ: [
                                     {"ts": 1234567890000, "values": {"temp": 25}},
                                     {"ts": 1234567891000, "values": {"temp": 26}}
                                 ]
        
        Returns:
            bool: True nếu push thành công, False nếu thất bại
            
        Example:
            >>> data_list = [
            ...     {"ts": 1234567890000, "values": {"temperature": 25}},
            ...     {"ts": 1234567891000, "values": {"temperature": 26}}
            ... ]
            >>> subscriber.push_multiple_telemetry(data_list)
            True
        """
        if not self.device_token:
            if not self.get_device_token():
                print("❗ Không thể lấy device token để push telemetry")
                return False

        telemetry_url = f"http://{self.host}:{self.rest_port}/api/v1/{self.device_token}/telemetry"
        headers = {
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(telemetry_url, json=telemetry_list, headers=headers, timeout=10)
            resp.raise_for_status()
            print(f"✅ Push multiple telemetry thành công: {len(telemetry_list)} records")
            return True
        except Exception as e:
            print(f"❗ Lỗi khi push multiple telemetry: {e}")
            return False

    def on_message(self, ws, message):
        """
        Xử lý message nhận được từ WebSocket ThingsBoard
        
        Args:
            ws: WebSocket instance
            message (str): Message JSON nhận được từ ThingsBoard
            
        Note:
            Method này được gọi tự động khi có dữ liệu telemetry mới
        """
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
            self.connected = True
        elif 'subscriptionId' in payload and payload.get('errorCode') == 0:
            print(f"✅ Đã kết nối telemetry subscription ID: {payload['subscriptionId']}")
            self.connected = True
        else:
            print("ℹ️ Message khác:", payload)

    def on_error(self, ws, error):
        """Add commentMore actions
        Xử lý lỗi WebSocket
        
        Args:
            ws: WebSocket instance
            error: Lỗi xảy ra
        """
        print("🚨 WebSocket error:", error)

    def on_close(self, ws, code, reason):
        """Add commentMore actions
        Xử lý khi WebSocket đóng kết nối
        
        Args:
            ws: WebSocket instance
            code (int): Mã lỗi đóng kết nối
            reason (str): Lý do đóng kết nối
        """
        print(f"🔒 WebSocket đóng (code={code}, reason={reason})")
        self.connected = False

    def on_open(self, ws):
        """Add commentMore actions
        Xử lý khi WebSocket mở kết nối thành công
        
        Args:
            ws: WebSocket instance
            
        Note:
            Tự động subscribe telemetry data khi kết nối thành công
        """
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
        """Add commentMore actions
        Khởi động kết nối WebSocket để subscribe telemetry data
        
        Note:
            - Tự động lấy JWT token và device token
            - Chạy WebSocket trong background thread
            - Method này không block main thread
        """
        if not self.token:
            self.get_jwt_token()

        if not self.device_token:
            self.get_device_token()
            
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
        """Add commentMore actions
        Lấy giá trị telemetry mới nhất theo key
        
        Args:
            key (str): Tên của telemetry key cần lấy
                      Ví dụ: "temperature", "humidity", "mq2", "dust"
        
        Returns:
            any: Giá trị telemetry tương ứng với key
            None: Nếu không tìm thấy key hoặc chưa có dữ liệu
            
        Example:
            >>> temp = subscriber.get_telemetry_value("temperature")
            >>> print(f"Temperature: {temp}°C")
        """
        return self.telemetry_data.get(key)

    def get_all_telemetry(self):
        """Add commentMore actions
        Lấy tất cả dữ liệu telemetry hiện có
        
        Returns:
            dict: Dictionary chứa tất cả telemetry data
                  Ví dụ: {"temperature": 25.5, "humidity": 60, "mq2": 10}
                  
        Example:
            >>> all_data = subscriber.get_all_telemetry()
            >>> for key, value in all_data.items():
            ...     print(f"{key}: {value}")
        """
        return dict(self.telemetry_data)


# Nếu file này được chạy trực tiếp, test nhanh kết nối và push telemetry
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
