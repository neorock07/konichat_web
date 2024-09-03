from turtle import onclick, width
from more_itertools import substrings
import streamlit as st
from dataclasses import dataclass
import time
import requests
from streamlit_lottie import st_lottie 
from streamlit_feedback import streamlit_feedback
import random
from annotated_text import annotated_text
import logging
from datetime import datetime
from navigation import make_sidebar
from rag.ensemble_rag import init_rag
import uuid
from streamlit_chat import message
import clipboard
from controller.feedback_method import feedback
from modelMsg.message_model import Message
from modelMsg.prompt_model import Prompt
from controller.inference import inference
from controller.copytext import on_copy_click
from controller.chat_controller import generate_response
from controller.chat_controller import save_chat_experimental
from controller.chat_controller import save_session_experimental
from controller.chat_controller import get_chat_experimental
from controller.chat_controller import get_session_experimental
from modelMsg.chat_model import ChatModel
from modelMsg.session_model import SessionModel
from datetime import datetime

st.set_page_config("KoniChat | Chat", page_icon="assets/fav.png")

logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex
    st.session_state[f"chat_history_{st.session_state.session_id}"] = []
    # st.session_state[f"chat_history"] = []
    st.session_state.set_fb = {}

if 'isSessionCreated' not in st.session_state:
    st.session_state.isSessionCreated = True
    
       
chat_list = None
session = None
rag_chain = None

if 'user_data' in st.session_state:
    data_login = st.session_state.user_data
    session = requests.Session()
    rag_chain = init_rag()
    chat_history = []
    chat_list = get_session_experimental(id=data_login['id'])
else:
    st.switch_page("login.py")    


if "copied" not in st.session_state: 
    st.session_state.copied = ""

    
ai_respon:str = ""
human_query:str = ""    
def handle_feedback():  
        ulasan = dict(st.session_state.fb_k)
        logger.debug(f"key ulasan : {ulasan.keys()}") 
        feedback(ulasan['score'], ulasan['text'], ai_respon, human_query)
        # if ulasan and 'type' in ulasan:
        # else:
        #     st.toast("❌ Review failed")
        logger.debug(f"lha iki coeg {ulasan}")


st.title(f"Hi, {data_login['username']}!")

st.sidebar.markdown("KoniChat | Chat").caption("KoniChat can make mistakes. Check important info.")
prompt: str = st.chat_input("chat disini!")

    
USER = "user"
AI = "assistant"
MESSAGES = "messages"

if 'run_id' not in st.session_state:
    st.session_state.run_id = uuid.uuid4().hex

if MESSAGES not in st.session_state:
    st.session_state[MESSAGES] = [Message(actor=AI, payload="Halo👋, saya KoniChat ada yang bisa saya bantu ?")]
    
msg: Message
for idx, msg in enumerate(st.session_state[MESSAGES]):
    # Use idx to create a unique key for each message widget
    message(
        msg.payload, 
        is_user=True if msg.actor == USER else False, 
        avatar_style='miniavs', 
        seed=msg.actor, 
        key=f"message_{idx}"  # Unique key for each message
    )

with st.sidebar:
    if isinstance(chat_list, list):
        for i in chat_list:
            st.button( i['title'] if len(i['title']) < 30 else str(i['title'])[:30] , use_container_width=True, key=uuid.uuid4().hex)
                
    
  
if prompt:
    
    human_query = prompt
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    # st.chat_message(USER, avatar="🧑").write(prompt)
    message(prompt, is_user= True, avatar_style='personas', seed=USER)
    
    with st.spinner("KoniChat sedang mengetik..."):
        # response, time_respon = predict(prompt)
        response, time_respon = inference(rag_chain, Prompt(query=human_query, role=data_login['role'], id=data_login['id']))
        ai_respon = response
        #tambah ke session messages
        st.session_state[MESSAGES].append(Message(actor=AI, payload=response))
        # st.session_state[MESSAGES].append(Message(actor=AI, payload=response))
        
        #tampilkan ke chatbox
        generate_response(Message(actor=AI, payload=response), time_respon=time_respon)
        today = datetime.today()
        formatted_time = today.strftime("%Y-%m-%d %H:%M:%S")
        
        # """
        #     cek sesi apakah sudah dibuat dan apakah sudah de-aktif,
        #     simpan jika masih kondisi true.
        # """
        
        if 'isSessionCreated' in st.session_state and st.session_state.isSessionCreated is True:
            save_session_experimental(SessionModel(
                id_session=f"chat_history_{st.session_state.session_id}",
                tanggal = formatted_time,
                title = prompt,
                id_user = data_login['id']
                ))
            
            st.session_state.isSessionCreated = False
        # """
        #     simpan data setiap kali percakapan
        # """
        save_chat_experimental(ChatModel(
            ai_respon=response,
            human_query=prompt,
            tanggal=formatted_time,
            id_session=f"chat_history_{st.session_state.session_id}"))
        
        chat_list = get_session_experimental(id=data_login['id'])
            
        
        # """
        #     form feedback akan tampil setiap ai selesai merespon
        # """
        with st.form('form'):
            feedbck = streamlit_feedback(feedback_type="thumbs",
                                optional_text_label="Berikan ulasanmu!", 
                                align="flex-start", 
                                key='fb_k')
            st.form_submit_button('Save feedback', on_click=handle_feedback)