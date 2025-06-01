from module import function_exAI
# from module import function_AI
# from module import mqttservice_coreiot
from module import httpservice_coreiot
import time

prev_value = None

def get_changed_attribute(attribute_key, attribute_type="shared", poll_interval=2):
    """
    Liên tục kiểm tra giá trị attribute từ ThingsBoard Cloud.
    Nếu phát hiện giá trị thay đổi thì trả về giá trị mới đó.
    :param attribute_key: Tên attribute cần kiểm tra
    :param attribute_type: Loại attribute ('shared' hoặc 'client')
    :param poll_interval: Thời gian lặp lại kiểm tra (giây)
    :return: Giá trị mới của attribute khi phát hiện thay đổi
    """
    global prev_value
    current_value = None
    while True:
        current_value = httpservice_coreiot.request_attribute(attribute_type, attribute_key)
        if current_value != prev_value:
            prev_value = current_value
            return current_value
        
        time.sleep(poll_interval)

def main():
    global prev_value
    prev_value = httpservice_coreiot.request_attribute("shared","Question")
    while True:
        time.sleep(2)
        # user_text = input("Bạn: ")
        # if user_text.strip().lower() in ["exit", "quit"]:
        #     break
        user_text = get_changed_attribute("Question")
        print("Giá trị mới của fan:", user_text)
        intent = function_exAI.parse_intent(user_text)
        device = intent.get("device")
        action = intent.get("action")
        # Sử dụng hàm control_device của chatbot để lấy response
        response = function_exAI.control_device(device, action, user_text)
        print("Chatbot:", response)
        
        # Sửa lại publish_attribute để đảm bảo đúng định dạng
        try:
            # mqttservice_coreiot.publish_attribute({'AI': response})
            httpservice_coreiot.publish_attribute({'AI': response})
        except Exception as e:
            print(f"Lỗi khi publish attribute: {e}")

if __name__ == "__main__":
    main()
