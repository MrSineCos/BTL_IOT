import os
import json
import re
# from module.mqttservice_coreiot import get_temperature, get_humidity, get_brightness, get_energy_consumption, turn_on_fan, turn_off_fan, turn_on_light, turn_off_light, status_fan, status_light
# from module.httpservice_coreiot import get_temperature, get_humidity, get_dust, get_gas, get_air
from module.ExternalAI_API import call_openrouter_chat, ask_openrouter_with_guide
from websocketAPI.telemetry_subscriber import TelemetrySubscriber

subscriber = TelemetrySubscriber()
subscriber.start()
valid_devices = [
    "DHT",  # cảm biến nhiệt độ độ ẩm
    "MQ",    # cảm biến khí gas
    "GP",   # cảm biến bụi
    "Air"   # chất lượng không khí
]
valid_actions = [
    "query_temperature", 
    "query_humidity", 
    "query_gas",
    "query_dust",
    "query_air",
    "general_question"  # Thêm loại hành động cho câu hỏi chung
]

def build_system_message():
    """
    Hệ thống sẽ mô tả nhiệm vụ NLU và schema JSON (Không được hỗ trợ nhưng vẫn hoạt động tốt).
    """
    return f"""You are an NLU module. Receive a English sentence, analyze it, and return a JSON object with 2 fields:
- device: the name of the device (one of {valid_devices}) or null
- action: one of {valid_actions} or null
If the user asks "temperature", the action is "query_temperature", and the device is "DHT".
If the user asks "humidity", the action is "query_humidity", and the device is "DHT".
If the user asks "gas", the action is "query_gas", and the device is "MQ".
If the user asks "dust", the action is "query_dust", and the device is "GP".
If the user asks "air", the action "query_air", and the device is "Air".
If the user asks about the system's capabilities, how to use the system, personal info or related to customer service, set action to "general_question" and device to null.
If it cannot be determined, return null for that field."""

def parse_intent(user_text: str) -> dict:
    schema = {
        "type": "object",
        "properties": {
            "device": {
                "type": ["string", "null"],
                "enum": valid_devices + [None]
            },
            "action": {
                "type": ["string", "null"],
                "enum": valid_actions + [None]
            }
        },
        "required": ["device", "action"]
    }
    messages = [
        {"role": "system", "content": build_system_message()},
        {"role": "user",   "content": user_text}
    ]
    content = call_openrouter_chat(messages, model="google/gemma-3-12b-it:free", stream=False)
    # Trích xuất JSON từ content trả về
    try:
        # Tìm đoạn JSON đầu tiên trong content
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            json_str = match.group(0)
            intent = json.loads(json_str)
        else:
            # Nếu không tìm thấy JSON, trả về mặc định
            intent = {"device": None, "action": None}
    except Exception as e:
        print(f"Error parsing intent JSON: {e}\nContent: {content}")
        intent = {"device": None, "action": None}
    return intent

def load_guide():
    guide_path = os.path.join(os.path.dirname(__file__), "guide.txt")
    if not os.path.exists(guide_path):
        return None
    with open(guide_path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_guide_answer(user_text, guide_data):
    if not guide_data:
        return None
    user_text_lower = user_text.lower()
    for key, items in guide_data.items():
        for item in items:
            if any(word in user_text_lower for word in item.lower().split()):
                return item
    return None

def ask_again(user_text):    
    guide_txt_path = os.path.join(os.path.dirname(__file__), "guide.txt")
    if os.path.exists(guide_txt_path):
        with open(guide_txt_path, "r", encoding="utf-8") as f:
            guide_content = f.read()
        try:
            # return ask_ollama_with_guide(user_text, guide_content).strip()
            return ask_openrouter_with_guide(user_text, guide_content, model="google/gemma-3-12b-it:free").strip()
        except Exception as e:
            print(f"Error when querying Ollama: {e}")
            return "Unable to retrieve information from the system guide."
    else:
        return "Guide file guide.txt not found."

def control_device(device, action, user_text=None):
    """
    Hàm mẫu để điều khiển thiết bị hoặc trả lời câu hỏi dựa trên intent.
    Trả về phản hồi dạng chuỗi.
    """
    if device == "DHT" and action == "query_temperature":
        temperature = subscriber.get_telemetry_value(key="temperature")
        return f"Temperature now is {temperature}°C." if temperature else "Unable to get temperature data."
    elif device == "DHT" and action == "query_humidity":
        humidity = subscriber.get_telemetry_value(key="humidity")
        return f"Humidity now is {humidity}%." if humidity else "Unable to get humidity data."
    elif device == "MQ" and action == "query_gas":
        gas = subscriber.get_telemetry_value(key="mq2")
        return f"Gas concentration compared to safety threshold now is {gas}%." if gas else "Unable to get gas data."
    elif device == "GP" and action == "query_dust":
        dust = subscriber.get_telemetry_value(key="dust")
        return f"Dust concentration now is {dust} mg/cm^3." if dust else "Unable to get dust data."
    elif device == "Air" and action == "query_air":
        temperature = subscriber.get_telemetry_value(key="temperature")
        humidity = subscriber.get_telemetry_value(key="humidity")
        gas = subscriber.get_telemetry_value(key="mq2")
        dust = subscriber.get_telemetry_value(key="dust")
        air_data = []
        try:
            # Tạo danh sách các giá trị có sẵn            
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
            
            print(f"Air information: {air_summary}")
            return f"{air_summary}." if air_summary else "Unable to get air info."
            
        except Exception as e:
            print(f"Lỗi lấy thông tin không khí: {e}")
            return None
    elif action == "general_question":
        guide_data = load_guide()
        # answer = find_guide_answer(user_text or "", guide_data)
        if guide_data:
            return (ask_again(user_text or ""))
        else:
            return ("The information you requested is not available. Please contact customer service for assistance.")
    else:
        return ("I don't understand your question.")

__all__ = ["parse_intent", "control_device", "load_guide", "find_guide_answer"]
