from module import function_exAI
from module import mqttservice_coreiot
import time
def main():
    while True:
        time.sleep(2)
        user_text = input("Bạn: ")
        if user_text.strip().lower() in ["exit", "quit"]:
            break
        intent = function_exAI.parse_intent(user_text)
        device = intent.get("device")
        action = intent.get("action")
        # Sử dụng hàm control_device của chatbot để lấy response
        response = function_exAI.control_device(device, action, user_text)
        print("Chatbot:", response)
        
        # Sửa lại publish_attribute để đảm bảo đúng định dạng
        try:
            mqttservice_coreiot.publish_attribute({'AI': response})
        except Exception as e:
            print(f"Lỗi khi publish attribute: {e}")

if __name__ == "__main__":
    main()
