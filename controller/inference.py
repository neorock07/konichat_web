from modelMsg.prompt_model import Prompt
import time
import logging
import streamlit as st


logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

# """
#     function untuk inference model, untuk melakukan conversation ke model.
#     params:
#         rag (Any) : isi dengan objek hasil assign ke RunnablePassThrough dan ke model LLM
#         input (Prompt) : field untuk menerima objek class Prompt sebagai pembungkus query ke model
#     returns:
#         respon (str) : hasil respon string model
#         response_time (float) : lama waktu respon model
# """

def inference(rag, input:Prompt):
    query = input.query
    role = input.role
    id = input.id
    
    # """
    #     cek apakah melanjutkan previous chat, atau mulai baru;
    #     jika lanjut, gunakan sesi previous, jika baru gunakan id session baru
    # """
    if 'continue_history' in st.session_state:
        chat_history = st.session_state[st.session_state.id_sesi_prev]
    else:
        chat_history = st.session_state[f"chat_history_{st.session_state.session_id}"]     
    if rag is None:
        return "error", 0  
    else:
            start_time = time.time()
            respon = ""
            
            logger.debug(f"len : {len(chat_history)} | {chat_history}")
            doc_retrieve = rag['retriever'].get_relevant_documents(query)
            
            respon = rag['rag_user'].invoke(
                        {
                            "question": query,
                            "chat_history": chat_history
                        }
                    )
                     
            if len(chat_history) >= 10:
                    chat_history.pop(0)
            else:
                    # """
                    #     tambahkan percakapan ke history model
                    # """    
                    chat_history.extend(
                            [
                                f"human question : {query}",
                                f"your answer : {respon}" 
                            ]
                        )
                    print("no memory")
            # """
            #     hitung lama respon model 
            # """           
            response_time = time.time() - start_time
            logger.debug(f"history : {chat_history}")
            logger.debug(f"len {len(doc_retrieve)} | dokumen ret : {doc_retrieve[0].page_content}")
            logger.debug(f"source document : {respon}")
    return respon.content,  doc_retrieve[0].page_content, response_time
    # return respon.content, response_time
    