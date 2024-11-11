import requests
import streamlit as st
import logging


logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

def feedback(tipe, feedback:str, ai_respon:str, query:str, role:int):
    """
        Function untuk mengirim data feedback ke server
        melalui REST API.
    """
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
        "feedback": feedback, 
        "id_role" : role
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

          
def get_count_feedback():
    """
    fungsi untuk mendapatkan jumlah feedback tipe Bad atau Good;
    """ 
    
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/feedback/count'
        
    try:
        # Melakukan POST request ke endpoint
        response = requests.get(url)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 200:
                # Mengambil respons JSON
                logger.debug("berhasil get feedback")
                return response.json()['data']
        else:
                logger.debug("gagal get feedback")
                st.toast("❌ Couldn't get feedback")
                return "error"    
    except Exception as e:
           logging.exception(e)


def get_bad_feedback(id_role:int):   
    """
    fungsi untuk mengambil data feedback user yang tipe BAD,
    untuk digunakan sebagai bahan membuat dokumen revisi untuk 
    fine tuning;
    
    Args:
        id_role (int) : id role user.
    """

     
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/feedback/get'
        
    try:
        data = {
            'id_role':id_role,
             }
        # Melakukan POST request ke endpoint
        response = requests.get(url, data=data)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 200:
                # Mengambil respons JSON
                logger.debug("berhasil get feedback")
                return response.json()['data']
        else:
                logger.debug("gagal get feedback")
                # st.toast("❌ Couldn't get feedback")
                return "error"    
    except Exception as e:
           logging.exception(e)
           
           