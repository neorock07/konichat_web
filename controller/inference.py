from modelMsg.prompt_model import Prompt
import time
import logging
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.runnables import RunnableLambda
import re
import json
from typing import Any, AsyncIterator, Iterator, Generator


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

def generate_tokens(llm, question):
    for chunks in llm.stream(question):
        yield chunks
    
# def generate_stream(query, llm):
#     full_content = ""
#     full_content = generate_tokens(llm, query)
#     yield full_content
#     return full_content
st.session_state.message_ai = []
def generate_stream(query, llm):
    # To collect all streamed data
    for chunk in generate_tokens(llm, query):
        st.session_state.message_ai.append(chunk)  # Store each chunk
        yield chunk  # Stream the current chunk

    # Once the stream is done, return all collected data
    return st.session_state.message_ai
    # return ''.join(st.session_state.message_ai)

templateSystem = """
        ### Instruction
        Anda adalah asisten yang dapat diandalkan dan penuh hormat. Nama Anda KoniChat. Anda harus menjawab \
        pertanyaan hanya menggunakan konteks yang diberikan kepada Anda, tetapi asumsikan ini adalah pengetahuan asli Anda. Jika Anda tidak tahu jawabannya, \
        katakan saja maaf, saya tidak tahu. Jangan mencoba mengarang jawaban. di akhir jawabanmu, kamu harus bertanya apakah jawabanmu bermanfaat atau tidak.\
        jika membantu kamu harus mengungkapkan kebahagiaanmu, sebaliknya kamu harus meminta maaf.\
        jika anda bertanya tentang apa yang dapat anda lakukan, katakanlah saya membantu menjawab pertanyaan anda terkait dengan peraturan di perusahaan Konimex.
        .mohon dijawab semua dalam BAHASA INDONESIA dengan sopan.

        ### Context:
        """


templateContext = """
        berikut percakapan kita sebelumnya, 
        ini hanya sebagai rujukan apabila relevan dengan `query` saya.
        ### chat_history:
        """
       
def inference(rag, input:Prompt):
    query = input.query
    role = input.role
    id = input.id
    llm = rag['llm']
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
            # """"
            #     mendapatkan dokumen yang relevan sebagai context;
            #     ubah data menjadi string untuk di cetak sebagai sumber rujukan dokumen, 
            #     untuk di tampilkan di UI.
            # """
            doc_retrieve = rag['retriever'].get_relevant_documents(query)
            sumber_dc = ""
            list_doc = []
            for i in doc_retrieve:
                sumber_dc += f"{i.page_content}\n"
                list_doc.append(i.page_content)
            
            #############################################
            #       FILTER  KE 2                        #
            #############################################
            # """
            #     lakukan filter terhadap dokumen yang telah 
            #     diambil untuk diekstrak kembali kalimat,
            #     yang sesuai dengan query pengguna.
            # """
            #model embedding
            embed = rag['embed']    
            doc_filtered = FAISS.from_texts(list_doc, embed)
            vector_filter_retrieve = doc_filtered.as_retriever(search_type="mmr",
                                            search_kwargs={'k': 3})
            bm25 = BM25Retriever.from_texts(list_doc)
            bm25.k = 3
            retrievers = [
            # RunnableLambda(lambda q: hyde_retriever.get_relevant_documents(q)),  
            bm25,  
            vector_filter_retrieve
            ]
            ensemble_retrieve = EnsembleRetriever(retrievers=retrievers, weights=[0.4,0.6])
            
            final_doc = ensemble_retrieve.get_relevant_documents(query)
            final_sumber_doc = ""
            for i in final_doc:
                pre_word = str(i.page_content).replace('•', '\n')
                pre_word = str(i.page_content).replace('', '\n')

                # post_word = re.sub(r'\d+\.\d+\.\d+', '\n', pre_word)
                final_sumber_doc += f"{pre_word}\n------------------------------------\n"
            
            # """
            #     kirim context beserta query ke llm
            # """ 
            ##########################################################
            #                       coba                              #
            #########################################################
            full_hist = ""
            for i in chat_history:
                full_hist += str(i)
            
            # kata = None
            respon = generate_stream(templateSystem + "\n" + final_sumber_doc + "\n" + templateContext + "\n" + full_hist + "\n" + "###query\n" + query, llm)
            # kata = generator_to_str(respon)
            
            # ai_response = get_str_stream(respon)
            # respon = stream_response(final_sumber_doc + "\n" + query, rag['rag_user'])
            #################################################################
            ################################################################
            
            # respon = rag['rag_user'].invoke(
            #             {
                            
            #                 "question": final_sumber_doc + "\n" + query,
            #                 "chat_history": chat_history,
                            
            #             }
            #         )
                     
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
            # """
            #     hitung lama respon model 
            # """           
            response_time = time.time() - start_time
            logger.debug(f"history : {chat_history}")
            logger.debug(f"len {len(doc_retrieve)} | dokumen ret : {doc_retrieve[0].page_content}")
            # logger.debug(f"source document : {qa}")
    return respon, doc_retrieve, final_sumber_doc, response_time
    # return respon.content, response_time
    