import datetime
import requests
import streamlit as st
import logging


logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

def feedback(tipe, feedback:str, ai_respon:str, query:str):
    type = ""
    if tipe == "👎":
        type = "BAD"
    else:
        type = "GOOD"    
    
    # Data yang akan dikirim ke endpoint
    data = {
        "tipe": type,
        "ai_respon":ai_respon, 
        "human_query":query,
        "feedback": feedback
        }
        
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/feedback/create'
        
    try:
            # Melakukan POST request ke endpoint
        response = requests.post(url, json=data)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 201:
                # Mengambil respons JSON
                logger.debug("berhasil insert feedback")
                st.toast("✔️ Feedback saved! Terima kasih")
        else:
                logger.debug("gagal insert feedback")
                st.toast("❌ Sorry, failed save feedback")

    except Exception as e:
           logging.exception(e)