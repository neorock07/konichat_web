import streamlit as st
import logging
from datetime import datetime
from rag.ensemble_rag import init_rag, invoke_rag
import uuid
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
import time
from widget.load_cookies import load_cookies
from widget.widget_feedback import widget_feedback
from widget.button_new_chat import button_new_chat
from widget.widget_chat import widget_chat, assignMessage
from widget.read_conversation import read_conversation
from widget.widget_chat_history import button_list_history
from widget.button_logout import button_logout

st.set_page_config("KoniChat | Chat", page_icon="assets/fav.png")

# """
#     inisiasi cookies manager
# """
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
    
st.sidebar.subheader("History Chat")
st.sidebar.divider()

# """
#    chatbox untuk tempat nge-prompt user
# """

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


# """
#     me-render ulang seluruh percakapan.
# """        
read_conversation()


# """
#     kode untuk ketika user ingin melanjutkan chat pada sesi sebelumnya;  
#     see:
#     kode untuk memuat previous chat dan assign ke session
#     yang akan digunakan ke memory model.
# """
id_session_history = None
    
# """
#     membuat list button untuk mengarahkan ke history chat.
# """    

button_list_history(chat_list, data_login['id'], id_session_history)

# """
#     membuat button logout
# """        
button_logout(cookies)

    
# """
#     jika human memulai percakapan
# """  
human_query = None


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