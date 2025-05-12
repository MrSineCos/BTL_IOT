import os
import json
import re
from module.mqttservice_coreiot import get_temperature, get_humidity, get_brightness, get_energy_consumption, turn_on_fan, turn_off_fan, turn_on_light, turn_off_light, status_fan, status_light
# from module.mqttservice_ada import get_temperature, get_humidity, get_brightness, get_energy_consumption, turn_on_fan, turn_off_fan, turn_on_light, turn_off_light
from module.ExternalAI_API import call_openrouter_chat, ask_openrouter_with_guide

valid_devices = [
    "light", 
    "fan",
    "photosensor",  # cảm biến ánh sáng
    "DHT",  # cảm biến nhiệt độ độ ẩm
    "PZEM"  # cảm biến điện năng
]
valid_actions = [
    "on", 
    "off",
    "status",
    "query_temperature", 
    "query_humidity", 
    "query_power",
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
If the user asks "brightness", the action is "query_brightness", and the device is "photosensor".
If the user asks "power consumption this month", the action is "query_power", and the device is "PZEM".
If the user asks "light status", the action is "status", and the device is "light".
If the user asks "fan status", the action is "status", and the device is "fan".
If the command is to turn on/off the light/fan, the action is "on"/"off", and the device is "light"/"fan".
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
    if action in ["on", "off", "status"]:
        # Điều khiển thiết bị thực tế
        if device == "fan":
            if action == "on":
                turn_on_fan()
                return "Đã bật quạt."
            elif action == "off":
                turn_off_fan()
                return "Đã tắt quạt."
            else:
                # Trang thái quạt
                status = status_fan()
                return f"Quạt hiện tại đang {'bật' if status else 'tắt'}."
            
        elif device == "light":
            if action == "on":
                turn_on_light()
                return "Đã bật đèn."
            elif action == "off":
                turn_off_light()
                return "Đã tắt đèn."
            else:
                # Trạng thái đèn
                status = status_light()
                return f"Đèn hiện tại đang {'bật' if status else 'tắt'}."
        else:
            return "Ko tìm thấy thiết bị."
    elif device == "DHT" and action == "query_temperature":
        temperature = get_temperature()
        return f"Temperature now is {temperature}°C." if temperature else "Unable to get temperature data."
    elif device == "DHT" and action == "query_humidity":
        humidity = get_humidity()
        return f"Humidity now is {humidity}%." if humidity else "Unable to get humidity data."
    elif device == "photosensor" and action == "query_brightness":
        brightness = get_brightness()
        return f"Brightness now is {brightness}." if brightness else "Unable to get brightness data."
    elif device == "PZEM" and action == "query_power":
        power = get_energy_consumption()
        return f"Power this month is {power} kWh." if power else "Unable to get power data."
    elif action == "general_question":
        guide_data = load_guide()
        # answer = find_guide_answer(user_text or "", guide_data)
        if guide_data:
            return (ask_again(user_text or ""))
        else:
            return ("The information you requested is not available. Please contact customer service for assistance.")
    else:
        return ("Cannot control device or answer question.")

__all__ = ["parse_intent", "control_device", "load_guide", "find_guide_answer"]
