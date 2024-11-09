import streamlit as st
from controller.chat_controller import get_conversation_by_id
from modelMsg.message_model import Message
from functools import partial
from datetime import datetime
import uuid

USER = "user"
AI = "assistant"
MESSAGES = "messages"
history_prev = []
@st.fragment
def load_chat_history(url_params, id_user, id_session_history):
    """
        function untuk mendapatkan data histori chat terdahulu 
        berdasarkan id_user yang sedang login pada session ini.
        
        - **params**:
               - url_params (str): alamat id histori chat e.g : `chat_history_3947hjdadaadas`
               - id_user (str) : id_user dari cookies atau data login.
               - id_session_history [list] : list kosong untuk menampung history yang diterima.
    """
    
    id_session_history = url_params
    st.query_params['c'] = url_params
    with st.spinner('loading...'):
        # """
        #     mendapatkan history chat berdasarkan id_session
        # """
        result = get_conversation_by_id(url_params, int(id_user))
        st.session_state[MESSAGES].clear()
        st.session_state.continue_history = True
        st.session_state.id_sesi_prev = id_session_history
        # """
        #     tambahkan ke session messages untuk dirender
        #     ke bentuk chatbox.
        # """
        if len(list(result['data'])) > 0:
            for id, data in enumerate(result['data']):
                st.session_state[MESSAGES].append(Message(actor=USER, payload=data['human_query']))
                st.session_state[MESSAGES].append(Message(actor=AI, payload=data['ai_respon'])) 
            
                history_prev.append(
                                    {
                                        "human_question" : data['human_query'],
                                        "your_answer" : data['ai_respon'] 
                                    }
                                )
        st.session_state[id_session_history] = history_prev        


def button_list_history(chat_list, id_user, id_session_history):
    """
        function untuk membuat list widget button yang akan 
        mengarahkan ke chat history yang di-klik.
        
    """
    
    if chat_list is not None:
        if len(chat_list) > 0:
            for i in chat_list:
                # Tanggal dalam format awal
                tanggal_awal = i['tanggal'][:10]
                # Mengonversi string ke objek datetime
                tanggal_obj = datetime.strptime(tanggal_awal, "%Y-%m-%d")
                # Mengonversi objek datetime ke string dalam format yang diinginkan
                tanggal_baru = tanggal_obj.strftime("%d %b %Y")
                st.sidebar.caption(tanggal_baru)
                st.sidebar.button(i['title'] if len(i['title']) < 30 else str(i['title'])[:30],
                                key=uuid.uuid4().hex,
                                use_container_width=True,
                                on_click=partial(load_chat_history, i['id_session'], id_user, id_session_history)
                                )
