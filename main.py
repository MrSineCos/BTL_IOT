from module import function_exAI
# from module import function_AI
# from module import mqttservice_coreiot
from module import httpservice_coreiot
import time

def main():
    prev_value = None
    while True:
        time.sleep(2)
        # user_text = input("Bạn: ")
        # if user_text.strip().lower() in ["exit", "quit"]:
        #     break
        user_text = httpservice_coreiot.request_attribute("shared","question").strip()
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
            print("Giá trị mới của fan:", user_text)
            lower_text = user_text.lower()
            # Check if all required keywords are present in user_text
            if all(word in lower_text for word in ['weather', 'predict']):
                try:
                    from weather_prediction import result
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
            httpservice_coreiot.publish_attribute({'answer': response})
        except Exception as e:
            print(f"Lỗi khi publish attribute: {e}")

if __name__ == "__main__":
    main()
