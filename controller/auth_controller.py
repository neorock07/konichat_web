import streamlit as st
import requests
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)


# """
#     function untuk login request ke server
#     params:
#         nik (int) : value nik 
#         password (str) : password user
#     returns:
#         result (true) : data user
#         error (false) : jika gagal menghubungi server    
# """
def login(nik, password):
    # Data yang akan dikirim ke endpoint
    data = {"nik": nik, "password": password}
    
    # URL endpoint FastAPI
    url = 'http://127.0.0.1:8000/api/login/'
    
    # Melakukan POST request ke endpoint
    response = requests.post(url, json=data)
    
    # Memeriksa apakah request berhasil
    if response.status_code == 200:
        # Mengambil respons JSON
        result = response.json()
        return result
    else:
        st.chat_message("Error", avatar="⚠️").write("Failed to get response from API")
        return "error"

