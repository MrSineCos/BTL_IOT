from module import function_exAI
# from module import function_AI
# from module import mqttservice_coreiot
# from module import httpservice_coreiot
from websocketAPI.telemetry_subscriber import TelemetrySubscriber
import time

subscriber = TelemetrySubscriber()
subscriber.start()
prev_value = None


def get_changed_telemetry(attribute_key, poll_interval=1):
    """
    Liên tục kiểm tra giá trị attribute từ ThingsBoard Cloud.
    Nếu phát hiện giá trị thay đổi thì trả về giá trị mới đó.
    :param attribute_key: Tên attribute cần kiểm tra
    :param attribute_type: Loại attribute ('shared' hoặc 'client')
    :param poll_interval: Thời gian lặp lại kiểm tra (giây)
    :return: Giá trị mới của attribute khi phát hiện thay đổi
    """
    global prev_value, subscriber
    current_value = None
    while True:
        current_value = subscriber.get_telemetry_value(attribute_key)
        if current_value != prev_value:
            prev_value = current_value
            return current_value
        
        time.sleep(poll_interval)

def main():
    global prev_value, subscriber
    while subscriber.isConnect is False:
        time.sleep(0.2)
    prev_value = subscriber.get_telemetry_value("Question")
    while True:
        time.sleep(2)
        # user_text = input("Bạn: ")
        # if user_text.strip().lower() in ["exit", "quit"]:
        #     break
        user_text = get_changed_telemetry("Question")
        print("Giá trị mới của Question:", user_text)
        intent = function_exAI.parse_intent(user_text)
        device = intent.get("device")
        action = intent.get("action")
        # Sử dụng hàm control_device của chatbot để lấy response
        response = function_exAI.control_device(device, action, user_text)
        print("Chatbot:", response)
        
        try:
            # mqttservice_coreiot.publish_attribute({'AI': response})
            # httpservice_coreiot.publish_attribute({'AI': response})
            subscriber.push_telemetry({"AI": response})
        except Exception as e:
            print(f"Lỗi khi publish attribute: {e}")

if __name__ == "__main__":
    main()
