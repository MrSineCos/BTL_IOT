import requests
import time
from typing import Optional, Dict, Any

# === Cấu hình ThingsBoard Cloud ===
THINGSBOARD_HOST = "app.coreiot.io"
THINGSBOARD_PORT = 1883
ACCESS_TOKEN = "X19l788unSsVNz5D6HTW"  # Thay bằng access token của thiết bị trên ThingsBoard
DEVICE_ID = "b25a5f30-2a51-11f0-a3c9-ab0d8999f561"  # Thay bằng deviceId của thiết bị trên ThingsBoard

# Thông tin đăng nhập để lấy JWT token
TENANT_USER = 'sinecoswifi@gmail.com'
TENANT_PASS = '123sc123'

# Biến lưu JWT token và thời gian hết hạn
_jwt_token = None
_token_expires_at = 0

def get_jwt_token(username: str = TENANT_USER, password: str = TENANT_PASS, force_refresh: bool = False) -> Optional[str]:
    """
    Đăng nhập qua REST API để lấy JWT Access Token.
    Token sẽ được cache và tự động refresh khi cần.
    
    :param username: Tên đăng nhập tenant
    :param password: Mật khẩu tenant
    :param force_refresh: Bắt buộc làm mới token
    :return: JWT token string hoặc None nếu lỗi
    """
    global _jwt_token, _token_expires_at
    
    # Kiểm tra token hiện tại còn hiệu lực không (trừ 5 phút để an toàn)
    current_time = time.time()
    if not force_refresh and _jwt_token and current_time < (_token_expires_at - 300):
        return _jwt_token
    
    login_url = f"http://{THINGSBOARD_HOST}/api/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        resp = requests.post(login_url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        token = data.get('token')
        if not token:
            print("❌ Không lấy được token từ ThingsBoard. Kiểm tra lại username/password.")
            return None
        
        # Lưu token và thời gian hết hạn (JWT thường có exp, nhưng ta estimate 1 giờ)
        _jwt_token = token
        _token_expires_at = current_time + 3600  # 1 giờ
        
        print(f"✅ Đã làm mới JWT token thành công")
        return token
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy JWT token: {e}")
        return None

def get_jwt_header() -> Dict[str, str]:
    """
    Lấy header Authorization với JWT token.
    Tự động refresh token nếu cần.
    
    :return: Dictionary chứa header Authorization
    """
    token = get_jwt_token()
    if not token:
        raise RuntimeError("Không thể lấy JWT token")
    
    return {"X-Authorization": f"Bearer {token}"}

def push_telemetry(data: dict, access_token: str = ACCESS_TOKEN) -> bool:
    """
    Gửi dữ liệu telemetry lên ThingsBoard Cloud.
    :param data: Dữ liệu telemetry dạng dict, ví dụ: {"temperature": 27}
    :param access_token: Access token của thiết bị
    :return: True nếu thành công, False nếu lỗi
    """
    url = f"http://{THINGSBOARD_HOST}/api/v1/{access_token}/telemetry"
    headers = {
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=5)
        resp.raise_for_status()
        print(f"✅ Đã gửi telemetry: {data}")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi telemetry: {e}")
        return False

def publish_attribute(data: dict, access_token: str = ACCESS_TOKEN) -> bool:
    """
    Cập nhật giá trị attribute lên ThingsBoard Cloud.
    :param data: Dữ liệu attribute dạng dict, ví dụ: {"AI": "hello sin"}
    :param access_token: Access token của thiết bị
    :return: True nếu thành công, False nếu lỗi
    """
    url = f"https://{THINGSBOARD_HOST}/api/v1/{access_token}/attributes"
    headers = {
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=5)
        resp.raise_for_status()
        print(f"✅ Đã cập nhật attribute: {data}")
        return True
    except Exception as e:
        print(f"❌ Lỗi cập nhật attribute: {e}")
        return False

def request_attribute(type: str, key: str, access_token: str = ACCESS_TOKEN) -> Optional[Any]:
    """
    Gửi yêu cầu lấy thuộc tính có tên key và loại là type (client, shared) từ ThingsBoard.
    """
    url = f"https://{THINGSBOARD_HOST}/api/v1/{access_token}/attributes"
    params = {}
    if type == "client":
        params["clientKeys"] = key
    elif type == "shared":
        params["sharedKeys"] = key
    else:
        print("❌ Loại attribute không hợp lệ. Chỉ hỗ trợ 'client' hoặc 'shared'.")
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
            print(f"❌ Không tìm thấy attribute '{key}' loại '{type}'")
            return None
    except Exception as e:
        print(f"❌ Lỗi lấy attribute '{key}' loại '{type}': {e}")
        return None

def get_latest_telemetry(key: str, device_id: str = DEVICE_ID) -> Optional[Any]:
    """
    Lấy giá trị telemetry mới nhất qua REST API (tự động sử dụng JWT token).
    """
    try:
        headers = get_jwt_header()
        url = f"https://{THINGSBOARD_HOST}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys={key}"
        
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        # Dữ liệu trả về dạng: {"temperature": [{"ts":..., "value":...}], ...}
        if key in data and isinstance(data[key], list) and data[key]:
            return data[key][0].get("value")
        else:
            print(f"❌ Không tìm thấy telemetry '{key}'")
            return None
    except Exception as e:
        print(f"❌ Lỗi lấy dữ liệu telemetry '{key}': {e}")
        return None

def get_telemetry_history(key: str, start_ts: int, end_ts: int, device_id: str = DEVICE_ID) -> Optional[list]:
    """
    Lấy lịch sử telemetry trong khoảng thời gian.
    
    :param key: Tên telemetry key
    :param start_ts: Timestamp bắt đầu (milliseconds)
    :param end_ts: Timestamp kết thúc (milliseconds)
    :param device_id: ID của thiết bị
    :return: List các giá trị telemetry hoặc None nếu lỗi
    """
    try:
        headers = get_jwt_header()
        url = f"https://{THINGSBOARD_HOST}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
        params = {
            "keys": key,
            "startTs": start_ts,
            "endTs": end_ts
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if key in data and isinstance(data[key], list):
            return data[key]
        else:
            print(f"❌ Không tìm thấy dữ liệu lịch sử cho '{key}'")
            return None
    except Exception as e:
        print(f"❌ Lỗi lấy lịch sử telemetry '{key}': {e}")
        return None

# Các hàm tiện ích để lấy dữ liệu sensor cụ thể
def get_temperature() -> Optional[str]:
    """Lấy giá trị temperature telemetry mới nhất."""
    return get_latest_telemetry("temperature")

def get_humidity() -> Optional[str]:
    """Lấy giá trị humidity telemetry mới nhất."""
    return get_latest_telemetry("humidity")

def get_dust() -> Optional[str]:
    """Lấy giá trị lượng bụi."""
    return get_latest_telemetry("dust")

def get_gas() -> Optional[str]:
    """Lấy giá trị khí gas."""
    return get_latest_telemetry("mq2")

def get_response() -> Optional[str]:
    """Lấy giá trị response mới nhất."""
    return get_latest_telemetry("response")

def get_air() -> Optional[str]:
    """
    Lấy giá trị chung của không khí bao gồm nhiệt độ, độ ẩm, lượng bụi và khí gas.
    :return: Chuỗi string chứa tất cả thông tin không khí hoặc None nếu lỗi
    """
    try:
        # Lấy tất cả giá trị cảm biến
        temperature = get_temperature()
        humidity = get_humidity()
        dust = get_dust()
        gas = get_gas()
        
        # Tạo danh sách các giá trị có sẵn
        air_data = []
        
        if temperature is not None:
            air_data.append(f"Temperature: {temperature}°C")
        else:
            air_data.append("temperature: N/A")
            
        if humidity is not None:
            air_data.append(f"Humidity: {humidity}%")
        else:
            air_data.append("Humidity: N/A")
            
        if dust is not None:
            air_data.append(f"Dust: {dust}")
        else:
            air_data.append("Dust: N/A")
            
        if gas is not None:
            air_data.append(f"Gas: {gas}")
        else:
            air_data.append("Gas: N/A")
        
        # Gộp tất cả thành một chuỗi
        air_summary = " | ".join(air_data)
        
        print(f"📊 Air information: {air_summary}")
        return air_summary
        
    except Exception as e:
        print(f"❌ Lỗi lấy thông tin không khí: {e}")
        return None

# Hàm test
def test_connection():
    """
    Test kết nối và các chức năng cơ bản.
    """
    print("🔧 Đang test kết nối ThingsBoard...")
    
    # Test JWT token
    token = get_jwt_token()
    if token:
        print(f"✅ JWT Token: {token[:50]}...")
    else:
        print("❌ Không thể lấy JWT token")
        return False
    
    # Test lấy thông tin không khí tổng hợp
    air_info = get_air()
    if air_info:
        print(f"✅ Thông tin không khí: {air_info}")
    else:
        print("❌ Không thể lấy thông tin không khí")
    
    # Test lấy telemetry riêng lẻ
    temp = get_temperature()
    if temp is not None:
        print(f"✅ Temperature: {temp}")
    else:
        print("❌ Không thể lấy temperature")
    
    # Test gửi telemetry
    test_data = {"test_connection": int(time.time())}
    if push_telemetry(test_data):
        print("✅ Test gửi telemetry thành công")
    else:
        print("❌ Test gửi telemetry thất bại")
    
    return True

if __name__ == "__main__":
    test_connection()