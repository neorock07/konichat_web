from warnings import deprecated
import requests
import logging
import streamlit as st

@deprecated
class ModelController:
    """
        Un-used controller, 
        develop it or remove it.
    """
    
    logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

    # Membuat logger
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        pass
    def predict(self, query):
        # Data yang akan dikirim ke endpoint
        data = {"prompt": query, "role": "user"}
        
        # URL endpoint FastAPI
        url = 'http://127.0.0.1:8000/predict'
        
        try:
            # Melakukan POST request ke endpoint
            response = requests.post(url, json=data)
            
            # Memeriksa apakah request berhasil
            if response.status_code == 200:
                # Mengambil respons JSON
                result = response.json()
                return result['content'], result['time']
            else:
                return "error", "no time"
        except Exception as e:
            logging.exception(e)
    
    def handle_feedback(self):  
        st.write(st.session_state.fb_k)
        st.toast("✔️ Feedback received!")        
                