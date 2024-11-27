import streamlit as st
from utils.utils import (
    log_event
)
import random
import time
import logging


logging.basicConfig(level=logging.INFO)




def send_prompt(multimodal_message, message_placeholder, generation_config, safety_settings, user_input, files_log):
    try:
        # raise ValueError("test error")
        response = st.session_state.chat_session.send_message(multimodal_message, 
                                                                generation_config=generation_config, 
                                                                safety_settings=safety_settings, 
                                                                stream=True)
        log_event(event_type="user-message", user_id=st.session_state.username, message=user_input, files=files_log)
        full_response = ""
        for chunk in response:
            word_count = 0
            random_int = random.randint(5,10)
            # random_int = 5
            for word in chunk.text:
                full_response+=word
                word_count+=1
                if word_count == random_int:
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + "_")
                    word_count = 0
                    random_int = random.randint(5,10)
        # for uri in files_uris:
        #     publish_pdf(uri, full_response)
        logging.info(f"===> assistant: {full_response}")
        log_event(event_type="model-response", user_id=st.session_state.username, response=full_response)
    except Exception as e:
        # st.exception(e)
        error_message = "😓 Disculpa! no entendí bien tu pregunta. ¿Podrías enviármela nuevamente? 🙏"
        # st.error(error_message)
        # print(f"Exception: {str(e)}")
        log_event(
            event_type="model-error",
            user_id=st.session_state.username,
            error_details=f"Exception: {str(e)}",
        )
        return error_message
    return full_response