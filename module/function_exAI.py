#   module/function_exAI.py
import os
import json
import re
# from module.httpservice_coreiot import get_temperature, get_humidity, get_dust, get_gas, get_air
from module.ExternalAI_API import call_openrouter_chat, ask_openrouter_with_guide
from websocketAPI.telemetry_subscriber import TelemetrySubscriber

# Khởi tạo subscriber để lấy dữ liệu telemetry từ WebSocket
subscriber = TelemetrySubscriber()
subscriber.start()

# Danh sách các thiết bị hợp lệ trong hệ thống IoT
valid_devices = [
    "DHT",  # Cảm biến nhiệt độ và độ ẩm (Digital Humidity & Temperature)
    "MQ",   # Cảm biến khí gas (Metal Oxide Semiconductor)
    "GP",   # Cảm biến bụi (General Purpose dust sensor)
    "Air"   # Tổng hợp chất lượng không khí
]

# Danh sách các hành động hợp lệ mà hệ thống có thể thực hiện
valid_actions = [
    "query_temperature",  # Truy vấn nhiệt độ
    "query_humidity",     # Truy vấn độ ẩm
    "query_gas",         # Truy vấn nồng độ khí gas
    "query_dust",        # Truy vấn nồng độ bụi
    "query_air",         # Truy vấn tổng hợp chất lượng không khí
    "general_question"   # Câu hỏi chung về hệ thống, hướng dẫn sử dụng
]

def build_system_message():
    """
    Xây dựng system message cho AI model để thực hiện Natural Language Understanding (NLU).
    
    Hàm này tạo ra một prompt hướng dẫn AI model phân tích câu nói của người dùng
    và trả về JSON object chứa thông tin về thiết bị và hành động cần thực hiện.
    
    Returns:
        str: System message chứa hướng dẫn cho AI model về cách phân tích intent
             và mapping từ câu nói sang device/action tương ứng
    
    Note:
        - Sử dụng JSON schema để đảm bảo format đầu ra nhất quán
        - Hỗ trợ cả câu hỏi về sensor data và câu hỏi chung về hệ thống
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
    """
    Phân tích ý định (intent) từ câu nói của người dùng bằng AI model.
    
    Hàm này sử dụng external AI API (OpenRouter) để phân tích câu nói tiếng Anh
    và trích xuất thông tin về thiết bị và hành động mà người dùng muốn thực hiện.
    
    Args:
        user_text (str): Câu nói/văn bản đầu vào từ người dùng
        
    Returns:
        dict: Dictionary chứa 2 key:
            - device (str|None): Tên thiết bị (DHT, MQ, GP, Air) hoặc None
            - action (str|None): Hành động cần thực hiện hoặc None
            
    Example:
        >>> parse_intent("What is the temperature?")
        {"device": "DHT", "action": "query_temperature"}
        
        >>> parse_intent("How to use this system?")
        {"device": None, "action": "general_question"}
    
    Note:
        - Sử dụng regex để trích xuất JSON từ response của AI
        - Có fallback mechanism khi parsing JSON thất bại
        - Model sử dụng: google/gemma-3-12b-it:free
    """
    # Định nghĩa JSON schema cho validation (hiện tại chỉ để tham khảo)
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
    
    # Tạo messages cho AI model
    messages = [
        {"role": "system", "content": build_system_message()},
        {"role": "user",   "content": user_text}
    ]
    
    # Gọi AI API để phân tích intent
    content = call_openrouter_chat(messages, model="google/gemma-3-12b-it:free", stream=False)
    
    # Trích xuất và parse JSON từ response
    try:
        # Tìm đoạn JSON đầu tiên trong content bằng regex
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            json_str = match.group(0)
            intent = json.loads(json_str)
        else:
            # Nếu không tìm thấy JSON, trả về giá trị mặc định
            intent = {"device": None, "action": None}
    except Exception as e:
        print(f"Error parsing intent JSON: {e}\nContent: {content}")
        intent = {"device": None, "action": None}
    
    return intent

def load_guide():
    """
    Tải file hướng dẫn hệ thống từ guide.txt.
    
    Hàm này đọc file guide.txt chứa thông tin hướng dẫn sử dụng hệ thống
    để phục vụ cho việc trả lời các câu hỏi chung của người dùng.
    
    Returns:
        dict|None: Dữ liệu JSON từ file guide.txt, hoặc None nếu file không tồn tại
                   hoặc có lỗi khi đọc file
    
    Note:
        - File guide.txt phải ở cùng thư mục với module này
        - File phải có format JSON hợp lệ
        - Sử dụng encoding UTF-8 để hỗ trợ tiếng Việt
    """
    guide_path = os.path.join(os.path.dirname(__file__), "guide.txt")
    if not os.path.exists(guide_path):
        return None
    
    try:
        with open(guide_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading guide file: {e}")
        return None

def find_guide_answer(user_text, guide_data):
    """
    Tìm kiếm câu trả lời phù hợp trong dữ liệu hướng dẫn dựa trên từ khóa.
    
    Hàm này thực hiện tìm kiếm đơn giản bằng cách so khớp từ khóa
    trong câu hỏi của người dùng với nội dung trong guide data.
    
    Args:
        user_text (str): Câu hỏi của người dùng
        guide_data (dict): Dữ liệu hướng dẫn đã được load từ file
        
    Returns:
        str|None: Câu trả lời phù hợp từ guide data, hoặc None nếu không tìm thấy
        
    Note:
        - Sử dụng keyword matching đơn giản (case-insensitive)
        - Có thể cần cải thiện thuật toán tìm kiếm cho độ chính xác cao hơn
        - Hiện tại chưa được sử dụng trong flow chính, được thay thế bởi AI-based search
    """
    if not guide_data:
        return None
    
    user_text_lower = user_text.lower()
    
    # Duyệt qua tất cả categories và items trong guide data
    for key, items in guide_data.items():
        for item in items:
            # Kiểm tra xem có từ nào trong item khớp với user text không
            if any(word in user_text_lower for word in item.lower().split()):
                return item
    
    return None

def ask_again(user_text):
    """
    Sử dụng AI để trả lời câu hỏi chung dựa trên nội dung file hướng dẫn.
    
    Hàm này đọc file guide.txt và sử dụng AI model để tạo ra câu trả lời
    phù hợp cho câu hỏi của người dùng dựa trên thông tin trong hướng dẫn.
    
    Args:
        user_text (str): Câu hỏi của người dùng
        
    Returns:
        str: Câu trả lời được tạo bởi AI dựa trên guide content,
             hoặc thông báo lỗi nếu không thể xử lý
             
    Example:
        >>> ask_again("How do I check temperature?")
        "To check temperature, you can ask 'What is the temperature?' and the system will..."
        
    Note:
        - Sử dụng model google/gemma-3-12b-it:free
        - Có error handling cho trường hợp file không tồn tại hoặc AI API lỗi
        - Kết quả được strip() để loại bỏ whitespace thừa
    """
    guide_txt_path = os.path.join(os.path.dirname(__file__), "guide.txt")
    
    if os.path.exists(guide_txt_path):
        try:
            # Đọc nội dung file hướng dẫn
            with open(guide_txt_path, "r", encoding="utf-8") as f:
                guide_content = f.read()
            
            # Sử dụng AI để tạo câu trả lời dựa trên guide content
            return ask_openrouter_with_guide(user_text, guide_content, model="google/gemma-3-12b-it:free").strip()
            
        except Exception as e:
            print(f"Error when querying AI with guide: {e}")
            return "Unable to retrieve information from the system guide."
    else:
        return "Guide file guide.txt not found."

def control_device(device, action, user_text=None):
    """
    Điều khiển thiết bị hoặc trả lời câu hỏi dựa trên intent đã được phân tích.
    
    Đây là hàm chính thực hiện các hành động cụ thể sau khi đã xác định được
    thiết bị và action từ câu nói của người dùng. Hàm sẽ lấy dữ liệu sensor
    hoặc trả lời câu hỏi chung tùy theo loại action.
    
    Args:
        device (str|None): Tên thiết bị (DHT, MQ, GP, Air) hoặc None
        action (str|None): Hành động cần thực hiện hoặc None  
        user_text (str, optional): Câu hỏi gốc của người dùng (dùng cho general_question)
        
    Returns:
        str: Phản hồi dạng text cho người dùng, bao gồm:
            - Giá trị sensor hiện tại (nhiệt độ, độ ẩm, khí gas, bụi)
            - Tổng hợp thông tin chất lượng không khí
            - Câu trả lời cho câu hỏi chung
            - Thông báo lỗi nếu không hiểu câu hỏi
            
    Example:
        >>> control_device("DHT", "query_temperature")
        "Temperature now is 25.5°C."
        
        >>> control_device("Air", "query_air")
        "Temperature: 25.5°C | Humidity: 60% | Dust: 0.02 mg/cm^3 | Gas: 15%."
        
        >>> control_device(None, "general_question", "How to use this system?")
        "This system allows you to monitor environmental conditions..."
    
    Note:
        - Sử dụng TelemetrySubscriber để lấy dữ liệu real-time từ WebSocket
        - Có xử lý trường hợp dữ liệu sensor không khả dụng (N/A)
        - Đối với query_air: tổng hợp tất cả thông tin môi trường
        - Đối với general_question: sử dụng AI để trả lời dựa trên guide
    """
    # Xử lý truy vấn nhiệt độ từ cảm biến DHT
    if device == "DHT" and action == "query_temperature":
        temperature = subscriber.get_telemetry_value(key="temperature")
        return f"Temperature now is {temperature}°C." if temperature else "Unable to get temperature data."
    
    # Xử lý truy vấn độ ẩm từ cảm biến DHT
    elif device == "DHT" and action == "query_humidity":
        humidity = subscriber.get_telemetry_value(key="humidity")
        return f"Humidity now is {humidity}%." if humidity else "Unable to get humidity data."
    
    # Xử lý truy vấn nồng độ khí gas từ cảm biến MQ
    elif device == "MQ" and action == "query_gas":
        gas = subscriber.get_telemetry_value(key="mq2")
        return f"Gas concentration compared to safety threshold now is {gas}%." if gas else "Unable to get gas data."

    # Xử lý truy vấn nồng độ bụi từ cảm biến GP
    elif device == "GP" and action == "query_dust":
        dust = subscriber.get_telemetry_value(key="dust")
        return f"Dust concentration now is {dust} mg/cm^3." if dust else "Unable to get dust data."
    
    # Xử lý truy vấn tổng hợp chất lượng không khí từ tất cả cảm biến
    elif device == "Air" and action == "query_air":
        # Lấy dữ liệu từ tất cả các cảm biến môi trường
        temperature = subscriber.get_telemetry_value(key="temperature")
        humidity = subscriber.get_telemetry_value(key="humidity")
        gas = subscriber.get_telemetry_value(key="mq2")
        dust = subscriber.get_telemetry_value(key="dust")
        air_data = []
        
        try:
            # Tạo danh sách các giá trị có sẵn với format phù hợp
            if temperature is not None:
                air_data.append(f"Temperature: {temperature}°C")
            else:
                air_data.append("Temperature: N/A")
                
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
            
            # Gộp tất cả thông tin thành một chuỗi với separator
            air_summary = " | ".join(air_data)
            
            print(f"Air information: {air_summary}")
            return f"{air_summary}." if air_summary else "Unable to get air info."
            
        except Exception as e:
            print(f"Lỗi lấy thông tin không khí: {e}")
            return "Error occurred while retrieving air quality information."
    
    # Xử lý câu hỏi chung về hệ thống, hướng dẫn sử dụng
    elif action == "general_question":
        guide_data = load_guide()
        # Sử dụng AI để trả lời dựa trên guide content thay vì keyword matching
        # answer = find_guide_answer(user_text or "", guide_data)
        if guide_data:
            return ask_again(user_text or "")
        else:
            return "The information you requested is not available. Please contact customer service for assistance."
    
    # Trường hợp không xác định được intent hoặc không hỗ trợ
    else:
        return "I don't understand your question."

# Định nghĩa các hàm được export từ module này
__all__ = ["parse_intent", "control_device", "load_guide", "find_guide_answer"]
