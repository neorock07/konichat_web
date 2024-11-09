from proto import MESSAGE
import streamlit as st
from streamlit_feedback import streamlit_feedback
import logging
from datetime import datetime
from rag.ensemble_rag import init_rag, invoke_rag
import uuid
from controller.feedback_method import feedback
from modelMsg.message_model import Message
from modelMsg.prompt_model import Prompt
from controller.inference import inference
from controller.chat_controller import generate_response
from controller.chat_controller import save_chat_experimental
from controller.chat_controller import save_session_experimental
from controller.chat_controller import get_session_experimental
from controller.chat_controller import get_conversation_by_id
from modelMsg.chat_model import ChatModel
from modelMsg.session_model import SessionModel
from datetime import datetime
from layout.custom_layout import st_fixed_container
from controller.auth_controller import logout
import time
from streamlit_cookies_manager import EncryptedCookieManager
import os
from widget.load_cookies import load_cookies
from widget.widget_feedback import widget_feedback
from widget.button_new_chat import button_new_chat
from widget.widget_chat import widget_chat, assignMessage
from widget.read_conversation import read_conversation
from widget.widget_chat_history import button_list_history
from widget.button_logout import button_logout
from functools import partial

st.set_page_config("KoniChat | Chat", page_icon="assets/fav.png")

# """
#     inisiasi cookies manager
# """

# cookies = EncryptedCookieManager(
#     prefix="konichat_chat",
#     password=os.environ.get("COOKIES_PASSWORD",
#                             #ini dapat diganti sesuai selera
#                             "adhakshdkah3783432hjshfsdjfjsdfjsgfq393274sdjhfs"),
# )

# if not cookies.ready():
#     # Menunggu Cookies mendapatkan data
#     st.spinner()
#     st.stop()
cookies = load_cookies()


logging.basicConfig(
    # Menentukan level logging
    level=logging.DEBUG,  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

# """
#     setiap halaman akan memiliki session_id yang berbeda.
# """

if "session_id" not in st.session_state:
    if 'c' in st.query_params:
        if 'chat_history_' in st.query_params['c']:
            url_param = str(st.query_params['c']).split('chat_history_')[1] 
            st.session_state.session_id = url_param
    else:        
        st.session_state.session_id = uuid.uuid4().hex
            
    st.session_state.session_id = uuid.uuid4().hex
    st.session_state[f"chat_history_{st.session_state.session_id}"] = []
    
        
if 'isSessionCreated' not in st.session_state:
    st.session_state.isSessionCreated = True

if "message_ai" not in st.session_state:
    st.session_state.message_ai = []
    
# """
#     inisiasi variabel yang dipakai.
# """    
chat_list = None
session = None
rag_chain = None
def_rag = None
def_rag = init_rag()

       
# """
#     inisiasi session baru, jika ke history chat pakai session yg lama.
#     init_rag -> proses embeddings dijalankan satu kali ketika streamlit di running.
# """

if 'id' in cookies and cookies['id'] is not '':
    data_login = dict(cookies)
    
    if 'rag_init' not in st.session_state:
        st.session_state.rag_init = True
        with st.spinner("membuat sesi baru..."):
            # """
            #     Assign hasil proses Embedding Dokumen ke invoke_rag 
            #     yang akan dipanggil setiap inferensi.
            # """
            rag_chain = invoke_rag(
                role=data_login['name_role'],
                chunked=def_rag['chunked'],
                feed_chunked=def_rag["feedback"],
                llm=def_rag['llm'], 
                embed=def_rag['embed'] 
                )
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

       
# def handle_feedback(ai_respon, human_query):
#         if st.session_state.fb_k is not None:  
#             ulasan = dict(st.session_state.fb_k)
#             feedback(ulasan['score'], ulasan['text'], ai_respon, human_query, data_login['role'])
#         else:
#             st.toast("Sorry, your feedback could not be saved!")     



# """
#     text untuk print username
# """
username = cookies['username']
st.title(f":rainbow[Hi, {username}!]")
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
button_new_chat(cookies, MESSAGES)
# if st.sidebar.button("New Chat 🌝"):
#     st.toast("🚀Starting New Chat")
#     # st.rerun()
#     st.query_params['c'] = "automodel"
#     cookies["message"] = ""
#     st.session_state[MESSAGES].clear()
#     del st.session_state.session_id
#     st.session_state.isSessionCreated = False
#     del st.session_state.isSessionCreated
#     time.sleep(3)
#     st.rerun()
    
st.sidebar.subheader("History Chat")
st.sidebar.divider()

# """
#     UI chat text-field
# """
# if st.session_state.rag_chain is not None:
#     prompt: str = st.chat_input("chat disini!")
# else:
#     prompt: str = st.chat_input("chat disini!", disabled=True)

prompt:str = widget_chat()    

greetings = "Halo👋, saya KoniChat ada yang bisa saya bantu ?"
if MESSAGES not in st.session_state:
    typing_area = st.empty()
    # Kecepatan mengetik dalam detik per karakter
    typing_speed = 0.01  
    displayed_text = ""
    
    for char in greetings:
        displayed_text += char
        typing_area.write(displayed_text)
        time.sleep(typing_speed)
    typing_area.empty()    
    st.session_state[MESSAGES] = [Message(actor=AI, payload=greetings)]

######################################################################
#     mendapatkan kembali tiap conversation menurut parameter url 
#
# misal : https://alamat_web/app?c=chat_history_67362338483
# maka data conversation akan diambil dari id 'chat_history_67362338483'
######################################################################

if 'c' in st.query_params:
    params_url = st.query_params["c"]
    if MESSAGES in st.session_state:
        st.session_state[MESSAGES].clear()
    
    
    # """
    #     pengecekan dilakukan untuk memastikan keamanan chat dari
    #     kebocoran data chat pada skenario user mengakses url chat 
    #     dari akun lain.
    #     misal:
    #        pemilik akun manager membuka chat dengan url tertentu, 
    #        kemudian akun karyawan mencoba untuk mengakses url chat 
    #        manager tersebut. agar data chat dari manager tidak dapat
    #        diakses oleh karyawan maka ditambahkan mekanisme kode berikut.
    # """
    if 'chat_history_' in params_url:
        result = get_conversation_by_id(params_url, int(data_login['id']))
        # st.info(result) 
        logger.debug(f"panjang result : {len(result['data'])}")
        if len(list(result['data'])) > 0:
            for id, data in enumerate(result['data']):
                    logger.debug(data)
                    st.session_state[MESSAGES].append(
                        Message(actor=USER, payload=data['human_query']))
                    st.session_state[MESSAGES].append(Message(actor=AI, payload=data['ai_respon'])) 
                    chat_history.append(
                                {
                                    "human_question" : data['human_query'],
                                    "your_answer" : data['ai_respon'] 
                                }
                            )
        elif len(list(result['data'])) < 0 and 'c' not in st.query_params:
            st.query_params['c'] = f"chat_history_{st.session_state.session_id}"    
                    
        else:
            if 'c' in st.query_params:
                if 'chat_history_' in st.query_params['c']:
                     id_from_url = st.query_params['c']   
                     st.session_state.session_id = str(id_from_url).split("chat_history_")[1]
                     st.query_params['c'] = f"chat_history_{uuid.uuid4().hex}"


        
# msg: Message
# @st.fragment
# def read_conversation(msg:Message):
#     for idx, msg in enumerate(st.session_state[MESSAGES]):
#         if msg.actor == AI:
#             st.chat_message(AI, avatar="assets/fav.png").write(msg.payload)
#         else:
#             st.chat_message(USER, avatar="📌").write(msg.payload)
#         if idx == (len(st.session_state[MESSAGES])-1) and 'final_doc' in st.session_state:
#             with st.expander("Sumber Dokumen"):
#                 st.write(st.session_state.final_doc)         
        

read_conversation()


# """
#     kode untuk ketika user ingin melanjutkan chat pada sesi sebelumnya;  
#     see:
#     kode untuk memuat previous chat dan assign ke session
#     yang akan digunakan ke memory model.
# """
id_session_history = None
# history_prev = []
# @st.fragment
# def print_log(msg, id_session_history):
#     logger.debug(msg)
#     id_session_history = msg
#     st.query_params['c'] = msg
#     with st.spinner('loading...'):
#         # """
#         #     mendapatkan history chat berdasarkan id_session
#         # """
#         result = get_conversation_by_id(msg, int(data_login['id']))
#         st.session_state[MESSAGES].clear()
#         st.session_state.continue_history = True
#         st.session_state.id_sesi_prev = id_session_history
#         # """
#         #     tambahkan ke session messages untuk dirender
#         #     ke bentuk chatbox.
#         # """
#         if len(list(result['data'])) > 0:
#             for id, data in enumerate(result['data']):
#                 st.session_state[MESSAGES].append(Message(actor=USER, payload=data['human_query']))
#                 st.session_state[MESSAGES].append(Message(actor=AI, payload=data['ai_respon'])) 
            
#                 history_prev.append(
#                                     {
#                                         "human_question" : data['human_query'],
#                                         "your_answer" : data['ai_respon'] 
#                                     }
#                                 )
#         st.session_state[id_session_history] = history_prev        
    
# """
#     membuat list button untuk mengarahkan ke history chat.
# """    

# if chat_list is not None:
#     if len(chat_list) > 0:
#         for i in chat_list:
#             # Tanggal dalam format awal
#             tanggal_awal = i['tanggal'][:10]
#             # Mengonversi string ke objek datetime
#             tanggal_obj = datetime.strptime(tanggal_awal, "%Y-%m-%d")
#             # Mengonversi objek datetime ke string dalam format yang diinginkan
#             tanggal_baru = tanggal_obj.strftime("%d %b %Y")
#             st.sidebar.caption(tanggal_baru)
#             st.sidebar.button(i['title'] if len(i['title']) < 30 else str(i['title'])[:30],
#                             key=uuid.uuid4().hex,
#                             use_container_width=True,
#                             on_click=partial(print_log, i['id_session'], id_session_history)
#                             )
                            # on_click=lambda msg=i['id_session']: print_log(msg))

button_list_history(chat_list, data_login['id'], id_session_history)

# """
#     membuat button logout
# """        
# with st.sidebar:
#     with st_fixed_container(mode="fixed", position="bottom", border=True, height=80, margin="bottom", key="asdasd"):
#             if st.button("Log out 📤", use_container_width=True):
#                 st.session_state[MESSAGES].clear()
#                 del st.session_state.session_id
#                 st.session_state.isSessionCreated = False
#                 del st.session_state.isSessionCreated
#                 del st.session_state.rag_init
#                 ###########################
#                 ##     hapus cookies     ##
#                 ##########################
#                 cookies['id'] = ""
#                 cookies['username'] = ""
#                 cookies['nik'] = "" 
#                 cookies['role'] = "" 
#                 cookies['name_role'] = ""
#                 cookies['message'] = ""
#                 cookies.save()
#                 logout()
#                 st.rerun()
button_logout(cookies)

# def widget_feedback(ai_respon, human_query, role):
#     with st.form('form'):
#         feedbck = streamlit_feedback(feedback_type="thumbs",
#                                      optional_text_label="Berikan ulasanmu!", 
#                                      align="flex-start", 
#                                      key='fb_k')
#         st.form_submit_button('Save feedback', 
#                               on_click=partial(handle_feedback, ai_respon, human_query, role))

                   
                  
    
    
# """
#     jika human memulai percakapan
# """  
human_query = None

# @st.fragment
# def assignMessage(prompt):
#     st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
#     st.chat_message(USER, avatar="📌").write(prompt)


if prompt:
    human_query = prompt
    assignMessage(human_query)
    task_txt = "KoniChat sedang mencari dokumen yang relevan..."
    with st.spinner(task_txt):
            
            # """
            #     tampung setiap return dari inference.py
            # """
            
        response, source_doc, final_doc,  time_respon = inference(st.session_state.rag_chain,
                                                                    Prompt(query=human_query, role=data_login['name_role'], 
                                                                        id=data_login['id']))
         
       
            # """
            #     tampilkan hasil respon Ai ke widget UI (token per token);
            #     agar mendapatkan respon lebih cepat < 5 detik;
            #     karena tidak menunggu jawaban full;
            # """
                
        ai_respon = generate_response(Message(actor=AI, payload=response), source_doc, final_doc, time_respon=time_respon)
        today = datetime.today()
        formatted_time = today.strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.final_doc = final_doc        
            # """
            # menggabungkan tiap token menjadi satu string;
            #   e.g : 'H', 'a', 'l' => 'Hallo';
            # lalu simpan ke session agar tetap ada ketika di-render ulang;
            # """ 
            
        ai_m = ''
        for i in st.session_state.message_ai:
            ai_m += i.content 
        
        st.session_state[MESSAGES].append(Message(actor=AI, payload=ai_m))
        
         # """
        #     simpan ke history chat
        # """
        if 'continue_history' in st.session_state:
                chat_history = st.session_state[st.session_state.id_sesi_prev]
        else:
                chat_history = st.session_state[f"chat_history_{st.session_state.session_id}"]
                # st.query_params['c'] = f"chat_history_{st.session_state.session_id}"      
                if 'c' in st.query_params:
                    if 'chat_history_' in st.query_params['c']:
                        id_from_url = st.query_params['c']   
                        st.session_state.session_id = str(id_from_url).split("chat_history_")[1]
                        
                st.query_params['c'] = f"chat_history_{st.session_state.session_id}"
        
        chat_history.append(
                                {
                                    "human_question" : human_query,
                                    "your_answer" : ai_m 
                                }
                            )
      
        # """
        #     menjaga agar hanya menampung 5 history percakapan
        # """
        if len(chat_history) > 5:
            chat_history = chat_history[:5]
        
        # st.info(chat_history)   

            # """
            #     cek sesi apakah sudah dibuat dan apakah sudah non-aktif,
            #     simpan jika kondisi masih true.
            # """
        # id_sesi = st.session_state.session_id
        id_sesi = st.query_params['c']
        if id_session_history is None:
            if 'isSessionCreated' in st.session_state and st.session_state.isSessionCreated is True:
                    save_session_experimental(SessionModel(
                        id_session=id_sesi,
                        # id_session=f"chat_history_{st.session_state.session_id}",
                        tanggal = formatted_time,
                        title = prompt,
                        id_user = data_login['id']
                        ))
            st.session_state.isSessionCreated = False
                    
        else:
            st.session_state.isSessionCreated = False
                        
            # """
            #     simpan data setiap kali percakapan, 
            #     dan hapus jawaban AI dari session sementara.
            # """
        if id_session_history is None:
                save_chat_experimental(ChatModel(
                    ai_respon=ai_m,
                    # ai_respon=response,
                    human_query=prompt,
                    tanggal=formatted_time,
                    id_session=id_sesi)
                                       )
                    # id_session=f"chat_history_{st.session_state.session_id}"))
                st.session_state.message_ai.clear()
        else:
                save_chat_experimental(ChatModel(
                    ai_respon=ai_m,
                    human_query=prompt,
                    tanggal=formatted_time,
                    id_session=id_session_history))
                st.session_state.message_ai.clear()
        
        with st.expander("chat history"):    
            st.write(f"{prompt}\n\n{ai_m}\n\n{formatted_time}\n\n{id_sesi}")        
            # """
            #     get new history session dari percakapan terkini
            # """        
        chat_list = get_session_experimental(id=data_login['id'])
            # """
            #     form feedback akan tampil setiap ai selesai merespon
            # """
        widget_feedback(ai_m, human_query, data_login['role'])              