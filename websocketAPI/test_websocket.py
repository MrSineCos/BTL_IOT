#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ví dụ Python: Subscribe Telemetry via WebSocket API của ThingsBoard

Các bước chính:
1. Đăng nhập (REST API) để lấy JWT Access Token.
2. Kết nối WebSocket (thuộc tính Telemetry Plugin).
3. Gửi payload subscribe (LATEST_TELEMETRY).
4. Nhận và xử lý dữ liệu telemetry trả về.

Chạy: python3 subscribe_telemetry.py
"""

import json
import threading
import time

import requests
# Import với tên khác để tránh xung đột tên file
import sys
import os

# Thêm đường dẫn để tránh xung đột import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import trực tiếp từ websocket-client package
    import websocket
    from websocket import WebSocketApp
    print("✅ Import WebSocket thành công")
except ImportError as e:
    print(f"❌ Lỗi import WebSocket: {e}")
    print("Hãy chạy: pip install websocket-client")
    exit(1)
except Exception as e:
    print(f"❌ Lỗi không xác định: {e}")
    exit(1)

# ----- CẤU HÌNH ThingsBoard -----
TB_HOST      = 'app.coreiot.io'          # Địa chỉ ThingsBoard của bạn
TB_REST_PORT = 80                             # 80 (HTTP) hoặc 443 (HTTPS) tùy cấu hình
TB_WS_PORT   = 80                             # 80 (WS) hoặc 443 (WSS) tùy cấu hình

TENANT_USER = 'sinecoswifi@gmail.com'    # Your email
TENANT_PASS = '123sc123'    # Your password

# Thay bằng Entity ID (UUID) của thiết bị bạn muốn subscribe
DEVICE_ID    = 'b25a5f30-2a51-11f0-a3c9-ab0d8999f561'


def get_jwt_token(host: str, port: int, username: str, password: str) -> str:
    """
    Đăng nhập qua REST API để lấy JWT Access Token.
    Trả về chuỗi token (string).
    """
    login_url = f"http://{host}:{port}/api/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    resp = requests.post(login_url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()  # Nếu có lỗi HTTP (4xx, 5xx) sẽ ném exception
    data = resp.json()

    token = data.get('token')
    if not token:
        raise RuntimeError("Không lấy được token từ ThingsBoard. Kiểm tra lại username/password.")
    return token


def on_message(ws, message):
    """
    Callback khi nhận được message từ ThingsBoard qua WebSocket.
    """
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        print("❗ Không parse được message JSON:", message)
        return

    # Kiểm tra nếu có subscriptionId và data (format ThingsBoard)
    if 'subscriptionId' in payload and 'data' in payload:
        subscription_id = payload['subscriptionId']
        error_code = payload.get('errorCode', 0)
        
        # Kiểm tra lỗi
        if error_code != 0:
            error_msg = payload.get('errorMsg', 'Unknown error')
            print(f"❌ Lỗi subscription {subscription_id}: {error_msg}")
            return
        
        # Xử lý dữ liệu telemetry
        data = payload['data']
        print(f"\n📡 Dữ liệu telemetry mới (Subscription ID: {subscription_id}):")
        print("-" * 60)
        
        for key, values in data.items():
            if isinstance(values, list) and len(values) > 0:
                # Mỗi value là một list [timestamp, value]
                for timestamp_ms, value in values:
                    # Chuyển timestamp từ milliseconds sang datetime
                    dt = time.strftime(
                        "%Y-%m-%d %H:%M:%S", 
                        time.gmtime(timestamp_ms / 1000.0)
                    )
                    print(f"  📊 {key:<15}: {value:<10} ({dt})")
        
        print("-" * 60)
        
    # Xử lý format cũ (nếu có ts và data trực tiếp)
    elif 'ts' in payload and 'data' in payload:
        ts_list = payload['ts']
        data_list = payload['data']

        for idx, timestamp in enumerate(ts_list):
            telemetry = data_list[idx]
            dt = time.strftime(
                "%Y-%m-%d %H:%M:%S", 
                time.gmtime(timestamp / 1000.0)
            )
            print(f"📥 [{dt}] -> {telemetry}")
    
    # Thông báo kết nối thành công
    elif 'subscriptionId' in payload and payload.get('errorCode') == 0:
        print(f"✅ Đã kết nối telemetry subscription ID: {payload['subscriptionId']}")
    
    else:
        # Các thông báo khác từ server
        print("ℹ️ Thông báo từ server:", payload)


def on_error(ws, error):
    """
    Callback khi WebSocket gặp lỗi.
    """
    print("🚨 WebSocket error:", error)


def on_close(ws, close_status_code, close_msg):
    """
    Callback khi WebSocket bị đóng.
    """
    print(f"🔒 WebSocket connection closed (code={close_status_code}, reason={close_msg})")


def on_open(ws):
    """
    Callback khi WebSocket kết nối thành công.
    Tại đây ta gửi payload subscribe để nhận telemetry.
    """
    print("🔌 WebSocket connection opened.")

    # Payload subscribe telemetry: LATEST_TELEMETRY
    subscribe_payload = {
        "tsSubCmds": [
            {
                "entityType": "DEVICE",
                "entityId": DEVICE_ID,
                "scope": "LATEST_TELEMETRY",
                "cmdId": 1
            }
        ]
    }
    ws.send(json.dumps(subscribe_payload))
    print("➡️  Đã gửi subscribe payload:", subscribe_payload)


def run_websocket(token: str):
    """
    Mở kết nối WebSocket đến ThingsBoard và lắng nghe telemetry.
    """
    # Sử dụng ws:// nếu không SSL, wss:// nếu có SSL (HTTPS)
    ws_url = f"ws://{TB_HOST}:{TB_WS_PORT}/api/ws/plugins/telemetry?token={token}"
    # Nếu sử dụng SSL (HTTPS) trên port 443, bạn thay bằng:
    # ws_url = f"wss://{TB_HOST}/api/ws/plugins/telemetry?token={token}"

    # Tạo WebSocketApp, gán callback
    ws_app = WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    # Chạy WebSocket trong một thread riêng để không chặn main thread
    wst = threading.Thread(target=ws_app.run_forever, kwargs={'ping_interval': 20, 'ping_timeout': 10})
    wst.daemon = True
    wst.start()

    try:
        while True:
            # Giữ chương trình chạy, người dùng có thể dừng bằng Ctrl+C
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Người dùng yêu cầu dừng. Đóng WebSocket...")
        ws_app.close()


def main():
    print("🔑 Bắt đầu đăng nhập và subscribe telemetry ThingsBoard...")

    try:
        token = get_jwt_token(TB_HOST, TB_REST_PORT, TENANT_USER, TENANT_PASS)
        print("✅ Đăng nhập thành công, Access Token (viết tắt):", token[:50], "...")
    except Exception as e:
        print("❌ Lỗi khi lấy token:", str(e))
        return

    # Sau khi có token, mở WebSocket và subscribe
    run_websocket(token)


if __name__ == "__main__":
    main()