from numpy import deprecate
from modelMsg.message_model import Message
import time
from .copytext import on_copy_click
from streamlit_chat import message
import streamlit as st
from annotated_text import annotated_text
import uuid
import threading
import requests
from modelMsg.chat_model import ChatModel
from modelMsg.session_model import SessionModel
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

USER = "user"
AI = "assistant"
MESSAGES = "messages"

"""
    function untuk menampilkan ke bentuk chatbox jika respon ai.
    
    params:
        msg (Message) : objek dari Message class, berisi actor dan payload message
        time_respon (float) : jumlah waktu yang respon model dalam menjawab.
    returns:
        None    
"""

@st.dialog("Sumber Dokumen")
def source_doc(item):
    st.write(f"{item}")
    if st.button("Submit"):
        st.rerun()
    

def generator_to_str(nested_generator) -> str:
    result = []
    for generator in nested_generator:  # Iterate over the outer generator
        for item in generator:  # Iterate over each inner generator
            result.append(str(item.content))  # Convert each item to string and append
    return ''.join(result) 

def generate_response(msg:Message, sumber, final_sumber ,time_respon:str):
    # token_full = ""
    typing_area = st.empty()
    # typing_speed = 0.01  # Kecepatan mengetik dalam detik per karakter
    # displayed_text = ""
    # for char in msg.payload:
    #     displayed_text += char
    #     typing_area.write(displayed_text)
    #     time.sleep(typing_speed)
    # with typing_area.chat_message(msg.actor, avatar="assets/fav.png").write(msg.payload)
    
    with typing_area.chat_message(msg.actor, avatar="assets/fav.png"):
        token_full = typing_area.write_stream(msg.payload)
   
    
    st.divider()
    # sumber_dc = ""
    # with st.expander("Sumber Dokumen"):
    #     for i in sumber:
    #         sumber_dc += i.page_content
    #     st.write(sumber_dc)
    
    with st.expander("Sumber Dokumen"):
        st.write(final_sumber)
    
    # st.info(sumber)
    # """
    #     button copy message & container waktu response model
    # """
    # st.button("📄", on_click=on_copy_click, args=(msg.payload, )) if msg.actor == AI else None
    annotated_text(
    ("waktu respon",f"{time_respon:.2f} s"),
    )
    
    
    return token_full

# """
#     fungsi untuk menyimpan pasangan chat human-Ai;
#     e.g: [{'human':'human answer..', 'Ai':'Ai response...'}];
#     params:
#         chat (ChatModel): objek ChatModel(ai_respon:str,
#                                 human_query:str,
#                                 tanggal:str,
#                                 id_session:str)
#     returns:
#         void;                            
# """

def save_chat_experimental(chat:ChatModel):
    ai_respon = chat.ai_respon
    human_query = chat.human_query
    tanggal = chat.tanggal
    id_session = chat.id_session
    
    # Data yang akan dikirim ke endpoint
    data = {
        "tanggal": tanggal,
        "ai_respon":ai_respon, 
        "human_query":human_query,
        "id_session" : id_session
        }
        
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/chat/create'
        
    try:
            # Melakukan POST request ke endpoint
        response = requests.post(url, json=data)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 201:
                # Mengambil respons JSON
                st.toast("✔️ Chat saved! Terima kasih")
        else:
                st.toast("❌ Sorry, failed save chat")

    except Exception as e:
           logging.exception(e)

# """
#     fungsi untuk medapatkan history chat menurut id_session;
#     params:
#         id (str): id_session
#     returns:
#         response (List[str]): list chat human dan Ai    
# """

def get_chat_experimental(id:str):
    data = {
        "id_session" : id
        }
        
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/chat/'
        
    try:
            # Melakukan POST request ke endpoint
        response = requests.get(url, json=data)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 200:
                # Mengambil respons JSON
                st.toast("✅ Berhasil memulihkan chat")
        else:
                st.toast("❌ Gagal memulihkan chat")
        return response

    except Exception as e:
           logging.exception(e) 

# """
#     fungsi untuk mendapatkan id_session yang telah disimpan;
#     params:
#         id (str) : id_user (nik)
#     returns:
#         response (List[str]): list id_session;  
# """
                     
def get_session_experimental(id:str):
    data = {
        "id_user" : id
        }
        
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/session/'
        
    try:
            # Melakukan POST request ke endpoint
        response = requests.get(url, json=data)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 200:
                # Mengambil respons JSON
            st.toast("✅ Berhasil memulihkan chat")
            # logger.debug(f"sesi : {response.json()}")
            return response.json()['data']
        else:
            st.toast("❌ Gagal memulihkan chat")
            return response

    except Exception as e:
           logging.exception(e)   
                   
def get_conversation_by_id(id:str):
    data = {
        "id_session" : id
        }
        
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/chat/id/'
        
    try:
            # Melakukan POST request ke endpoint
        response = requests.get(url, json=data)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 200:
                # Mengambil respons JSON
            st.toast("✅ Berhasil memulihkan chat")
            logger.debug(f"sesi : {response.json()}")
            return response.json()['data']
        else:
            st.toast("❌ Gagal memulihkan chat")
            return response

    except Exception as e:
           logging.exception(e)           

def save_session_experimental(data:SessionModel):
    id_session = data.id_session
    tanggal = data.tanggal
    title = data.title 
    id_user = data.id_user
    
    data = {
           "id_session" : id_session,
           "tanggal" : tanggal,
           "title" : title,
           "id_user" : id_user
        }
        
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/session/create'
        
    try:
            # Melakukan POST request ke endpoint
        response = requests.post(url, json=data)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 201:
                # Mengambil respons JSON
                st.toast("✅ Sesi Baru")
        else:
                st.toast("❌ Gagal Sesi Baru")
        return response

    except Exception as e:
           logging.exception(e)
    
async def periodic_send(chat:ChatModel):
    while True:
        if 'active_session' in st.session_state and st.session_state.active_session:
            save_chat_experimental(chat)
        time.sleep(180)

def start_session():
    if 'active_session' not in st.session_state:
        st.session_state.active_session = True
        st.toast("💚 New Session")
        threading.Thread(target=periodic_send, daemon=True).start()

def stop_session():
    st.session_state.active_session = False
    st.toast("💔 End Session")
            
                    
                