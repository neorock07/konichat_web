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
from controller.chat_controller import get_conversation_by_id
from modelMsg.chat_model import ChatModel
from modelMsg.session_model import SessionModel
from datetime import datetime
from functools import partial
from layout.custom_layout import st_fixed_container
from controller.auth_controller import logout
from layout.feedback_layout import feedback_form

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

if 'isSessionCreated' not in st.session_state:
    st.session_state.isSessionCreated = True
    
chat_list = None
session = None
rag_chain = None


       
# """
#     inisiasi session baru, jika ke history chat pakai session yg lama.
#     init_rag -> proses embeddings dijalankan satu kali ketika streamlit di running.
# """
if 'user_data' in st.session_state:
    data_login = st.session_state.user_data
    # with st.spinner("loading menyiapkan dokumen..."):
    #     rag_chain = init_rag()
    if 'rag_init' not in st.session_state:
        st.session_state.rag_init = True
        with st.spinner("loading menyiapkan dokumen..."):
            # rag_chain = init_rag()
            rag_chain = init_rag(data_login['role'])
            st.session_state.rag_chain = rag_chain
        logger.debug(f"RAG SEDANG INIT | {rag_chain.__class__}")
    else:
        logger.debug(f"RAG TELAH INIT | {rag_chain.__class__}")        
    chat_history = []
    chat_list = get_session_experimental(id=data_login['id'])
# """
#     redirect ke halaman login jika user belum login / sesi belum dibuat.
# """
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
        logger.debug(f"lha iki coeg {ulasan}")

# """
#     text untuk print username
# """
st.title(f":rainbow[Hi, {data_login['username']}!]")
st.markdown(
    """
    <style>
    .fixed-container {
        position: fixed;
        bottom: 20px; /* Atur sesuai kebutuhan */
        width: 100%;  /* Memastikan container memenuhi lebar sidebar */
    }
    </style>
    """, unsafe_allow_html=True
)
# """
#     constanta, sebagai key session message dan actor message
# """    
USER = "user"
AI = "assistant"
MESSAGES = "messages"

# """
#     kode untuk layout sidebar profile and button new chat, 
#     ketika new chat, hapus semua history chat terkini pada session
# """
st.sidebar.markdown(f"<p style='font-size:60px;' >{data_login['username']}</p>", unsafe_allow_html=True)
st.sidebar.markdown("KoniChat | Chat").caption("KoniChat can make mistakes. Check important info.")
if st.sidebar.button("New Chat ✒"):
    st.toast("new chat")
    st.query_params['c'] = "automodel"
    st.session_state[MESSAGES].clear()
    del st.session_state.session_id
    st.session_state.isSessionCreated = False
    del st.session_state.isSessionCreated

    
st.sidebar.subheader("History Chat")
st.sidebar.divider()
# """
#     UI chat text-field
# """
prompt: str = st.chat_input("chat disini!")



if 'run_id' not in st.session_state:
    st.session_state.run_id = uuid.uuid4().hex

if MESSAGES not in st.session_state:
    st.session_state[MESSAGES] = [Message(actor=AI, payload="Halo👋, saya KoniChat ada yang bisa saya bantu ?")]
    
msg: Message
for idx, msg in enumerate(st.session_state[MESSAGES]):
    # Use idx to create a unique key for each message widget
    if msg.actor == AI:
        st.chat_message(AI, avatar="assets/fav.png").write(msg.payload)
    else:
        st.chat_message(USER, avatar="👩‍🦲").write(msg.payload)
      

# """
#     kode untuk load previous chat dan assign ke session
#     yang akan digunakan ke memory model.
# """
id_session_history = None
history_prev = []
def print_log(msg):
    logger.debug(msg)
    # st.toast(msg)
    id_session_history = msg
    st.query_params['c'] = msg
    with st.spinner('loading...'):
        logger.debug(f"sesi prev session : {id_session_history}")
        # """
        #     mendapatkan history chat berdasarkan id_session
        # """
        result = get_conversation_by_id(msg)
        st.session_state[MESSAGES].clear()
        st.session_state.continue_history = True
        st.session_state.id_sesi_prev = id_session_history
        # """
        #     tambahkan ke session messages untuk dirender
        #     ke bentuk chatbox.
        # """
        for id, data in enumerate(result):
            st.session_state[MESSAGES].append(Message(actor=USER, payload=data['human_query']))
            st.session_state[MESSAGES].append(Message(actor=AI, payload=data['ai_respon'])) 
            history_prev.extend(
                [
                    f"human question : {data['human_query']}",
                    f"your answer : {data['ai_respon']}",
                ]
            )
        st.session_state[id_session_history] = history_prev        
    
# """
#     membuat list button untuk mengarahkan ke history chat.
# """    
if len(chat_list) > 0:
    for i in chat_list:
        st.sidebar.button(i['title'] if len(i['title']) < 30 else str(i['title'])[:30],
                        key=uuid.uuid4().hex,
                        use_container_width=True,
                        on_click=lambda msg=i['id_session']: print_log(msg))

# """
#     membuat button logout
# """        
with st.sidebar:
    with st_fixed_container(mode="fixed", position="bottom", border=True, height=80, margin="bottom", key="asdasd"):
            if st.button("Log out 📤", use_container_width=True):
                st.session_state[MESSAGES].clear()
                del st.session_state.session_id
                st.session_state.isSessionCreated = False
                del st.session_state.isSessionCreated
                del st.session_state.rag_init
                logout()
                st.rerun()
                   
    
# """
#     jika human memulai percakapan
# """  
if prompt:
    
    human_query = prompt
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    # message(prompt, is_user= True, avatar_style='personas', seed=USER)
    st.chat_message(USER, avatar="📌").write(prompt)
    
    with st.spinner("KoniChat sedang mengetik..."):
        response, source_doc, final_doc,  time_respon = inference(st.session_state.rag_chain, Prompt(query=human_query, role=data_login['name_role'], id=data_login['id']))
        # response, time_respon = inference(rag_chain, Prompt(query=human_query, role=data_login['role'], id=data_login['id']))
        ai_respon = response
        #tambah ke session messages
        st.session_state[MESSAGES].append(Message(actor=AI, payload=response))
        
        #tampilkan ke chatbox
        generate_response(Message(actor=AI, payload=response), source_doc, final_doc, time_respon=time_respon)
        today = datetime.today()
        formatted_time = today.strftime("%Y-%m-%d %H:%M:%S")
        
        # """
        #     cek sesi apakah sudah dibuat dan apakah sudah de-aktif,
        #     simpan jika masih kondisi true.
        # """
        if id_session_history is None:
            if 'isSessionCreated' in st.session_state and st.session_state.isSessionCreated is True:
                save_session_experimental(SessionModel(
                    id_session=f"chat_history_{st.session_state.session_id}",
                    tanggal = formatted_time,
                    title = prompt,
                    id_user = data_login['id']
                    ))
            st.session_state.isSessionCreated = False
                
        else:
            st.session_state.isSessionCreated = False
                    
        # """
        #     simpan data setiap kali percakapan
        # """
        if id_session_history is None:
            save_chat_experimental(ChatModel(
                ai_respon=response,
                human_query=prompt,
                tanggal=formatted_time,
                id_session=f"chat_history_{st.session_state.session_id}"))
        else:
            save_chat_experimental(ChatModel(
                ai_respon=response,
                human_query=prompt,
                tanggal=formatted_time,
                id_session=id_session_history))
        # """
        #     get new history chat dari percakapan terkini
        # """        
        chat_list = get_session_experimental(id=data_login['id'])
            
        
        # """
        #     form feedback akan tampil setiap ai selesai merespon
        # """
        # feedback_form()
        with st.form('form'):
            feedbck = streamlit_feedback(feedback_type="thumbs",
                                optional_text_label="Berikan ulasanmu!", 
                                align="flex-start", 
                                key='fb_k')
            st.form_submit_button('Save feedback', on_click=handle_feedback)