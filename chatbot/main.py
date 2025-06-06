from module import function_exAI
# from module import function_AI
# from module import mqttservice_coreiot
from websocketAPI.telemetry_subscriber import TelemetrySubscriber
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

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
        if user_text == "":
            if prev_value != "":
                response = "Please enter a valid question."
                prev_value = user_text
            elif user_text == prev_value:
                continue
        else:
            if prev_value == user_text:
                continue
            else:
                prev_value = user_text
            print("Giá trị mới của Question:", user_text)
            lower_text = user_text.lower()
            # Check if all required keywords are present in user_text
            if all(word in lower_text for word in ['weather', 'predict']):
                try:
                    from prediction.weather_prediction import result
                    response = result()
                except Exception as e:
                    print(f"Error while calling weather prediction: {e}")
                    return "Unable to predict today's weather at the moment."
            else:
                if user_text == "predict":
                    response = "What do you want to predict? Please specify."
                elif user_text == "today":
                    response = "Do you want to know the weather forecast for today?"
                else:
                    intent = function_exAI.parse_intent(user_text)
                    device = intent.get("device")
                    action = intent.get("action")
                    # Sử dụng hàm control_device của chatbot để lấy response
                    response = function_exAI.control_device(device, action, user_text)
        print("Chatbot:", response)
        
        # Sửa lại publish_attribute để đảm bảo đúng định dạng
        try:
            # mqttservice_coreiot.publish_attribute({'AI': response})
            subscriber.push_telemetry({"AI": response})
        except Exception as e:
            print(f"Lỗi khi publish attribute: {e}")

if __name__ == "__main__":
    main()
