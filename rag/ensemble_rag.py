from . chunk import split_docs, EOSSplitter
from .embedd_data import create_embeddings_by_texts, load_embedding_model, create_embeddings, load_retriever, load_retriever_feed
from .load_data import load_pdf_data
from .utils_context import Utils_context
import logging
from langchain_community.chat_models.ollama import ChatOllama
from langchain_community.chat_models.openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.retrievers.document_compressors import FlashrankRerank
from langchain.retrievers import ContextualCompressionRetriever
from dataclasses import dataclass
import time
import streamlit as st
from controller.document_controller import download_doc, get_all_docs, get_by_id_docs, get_feedback_doc
from langchain_core.documents.base import Document
from langchain.callbacks.base import BaseCallbackHandler
from pathlib import Path

# Mengatur konfigurasi logging
logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

def join_doc(docs):
    return "\n\n".join(doc for doc in docs)

rag_dic = None
file_path_manager = None
file_path_user = None

# """
#     mengambil seluruh data dokumen;
#     tujuan : `mengambil data semua lalu process satu waktu`
# """

def load_downloaded_file():
    global file_path_manager
    global file_path_user
    docs_all = get_all_docs()
    path_docs_dict = []
    role_set = []
    for i in docs_all:
        path_docs_dict.append(download_doc(i['file'], i['title']))  
        role_set.append(i['name'])
    
    ####################################################
    #            Feedback document                    #
    ################################################### 
    docs_feedback = get_feedback_doc()
    path_feed_doc = []
    if docs_feedback is not [] or docs_feedback is not None:
        for i in docs_feedback:
            data = {
              "role_name" :  i['name'],
              "path" :  download_doc(i['file'], i['title'])
            }
            path_feed_doc.append(data) 

    return path_docs_dict, role_set, path_feed_doc


# """
#     DO NOT USE THIS FUNCTION   
#     gunakan ini untuk mendownload 1 document sesuai role user yang login;    
#     mengambil seluruh data dokumen;
#     tujuan : `mengambil data sesuai role lalu process`
#     cons : `time consume minim hanya 1 doc`
# """

def load_downloaded_file_byId(role):
    docs = get_by_id_docs(role)
    logger.debug(f"docs download : {docs}") 
    file_path = download_doc(docs['file'], docs['title'])
    return file_path

# """
#     fungsi untuk memproses embedding dokumen dan menyimpannya menjadi 
#     objek FAISS untuk masing-masing role;
#     e.g: role manager -> (docA, docB) -> vectorstore_manager.pkl
#     proses ini disimpan dalam cache see: @st.cache_data;
#     sehingga proses ini dilakukan hanya ketika kode aplikasi pertama kali dijalankan;
#     note : agar caching dapat berjalan nama parameter diawali underscore e.g: _paramsA;
#     params:
#         _embed: model embedding untuk mengubah string to vector base;
#         _llm: model text generation (ChatOllama);
#     returns:
#         doc_chunked (dict[int, list[Document]]): dictionary hasil split document masing-masing role;
#             e.g: {'manager': [['isi konten A....'], ['isi konten B....']]}    
# """

 
@st.cache_data
def chunked_doc(_embed, _llm,):
    
    # """
    #     kode untuk memproses chunk sumber documents
    # """
    doc_chunked: dict[int, list[str]] = {}
    doc_path, roles, doc_feedback_path = load_downloaded_file()
    roles = list(roles)
    
    # Mengelompokkan dokumen berdasarkan role
    group_doc = {}
    for i in range(len(doc_path)):
        if roles[i] not in group_doc:
            group_doc[roles[i]] = []
        group_doc[roles[i]].append(doc_path[i])      
    
    # Membagi dokumen menjadi chunk dan menyimpannya di doc_chunked
    for i in group_doc:
        documents: list[str] = []
        full_pdf = ""
        pdfs = None
        list_pdf_content = []
        for j in group_doc[i]:
            docs = load_pdf_data(file_path=j)
            ##############################################
            #              split document sumber         #
            ##############################################
            for g in docs:
                # full_pdf += g.page_content
                full_pdf += f"Metadata Dokumen: {g.metadata['source']}\n\n{g.page_content}\n\n" 
            pdfs = full_pdf.split("<EOS>")
            for mj in pdfs:
                list_pdf_content.append(mj)
            
            documents.extend(list_pdf_content)  
        if i not in doc_chunked:
            doc_chunked[i] = []
        
        # Menggunakan extend agar tidak membuat list di dalam list
        doc_chunked[i].extend(documents)
    
    # Membuat embeddings untuk setiap dokumen yang sudah di-chunk
    for i in doc_chunked:
        create_embeddings_by_texts(doc_chunked[i], _embed, storing_path=f"vectorstore_{i}")
    ############################################################
    #               Chunk Document Feedback                   #
    ##########################################################
    
    dict_feed:dict[str, list[Document]] = {}
    chunk_eos = EOSSplitter(chunk_size=1200, chunk_overlap=300)
    if doc_feedback_path is not [] or doc_feedback_path is not None:
        # Membuat chunk untuk document feedback
        for i in doc_feedback_path:
            doc_feed = load_pdf_data(file_path = i['path'])
            feed_chunked = chunk_eos.split_documents(documents = doc_feed)
            dict_feed[i['role_name']] = feed_chunked
            # membuat embedding untuk dokumen revisi feedback
            create_embeddings(_llm, feed_chunked, _embed, storing_path=f"vectorstore_feedback_{i['role_name']}")    
            
    return doc_chunked, dict_feed    

# """
#     callback untuk ChatOllama class;
# """

class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.partial_output = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.partial_output += token
        print(token, end="", flush=True)
        
        
def generate_stream_tokens(llm, question):
    for chunk in llm.stream(question):
        yield chunk.content 


@st.cache_data
def init_rag():
    global rag_dic
    
    # """
    #     comment below code if you prefer to use OpenAI instead.
    # """  
    llm = ChatOllama(model="gemma_8192:latest", 
                     temperature=0.6,
                     base_url="https://ece1-34-127-10-173.ngrok-free.app")
    
    # """
    #     uncomment this code if you use OpenAI services instead.
    # """
    # llm = ChatOpenAI(model="gpt-4", temperature=0, api_key="kx-shuhs")
    
    # membuat objek embedding dari model all-MiniLM-L6-v2 [HUGGING_FACE's Model]
    embed = load_embedding_model(model_path="all-MiniLM-L6-v2")
    logger.debug("download embedding finished") 
    
    #paggil fungsi ini untuk melakukan proses embedding
    # note: default value feed_chunked = {}
    chunked, feed_chunked = chunked_doc(embed, llm)
    
    if feed_chunked is {}:
        feed_chunked = None
        
    return {
        "llm" : llm,
        "chunked" : chunked,
        "feedback" : feed_chunked, 
        "embed" : embed
    }
    
    
# """
#     fungsi untuk mendapatkan prediction words dari model LLM;
#     params:
#         role (str) : role user
#         chunked (dict(list, List[str])): dictionary hasil split document masing2 role;
#         feed_chunked (dict(list, List[Document])): dictionary hasil split document feedback masing2 role;
#         llm: model llm ChatOllama
#         embed : model embedding
#     returns:
#         rag_dic (dict)    
#
##   NOTE: kode digunakan di file app.py
# """
  
def invoke_rag(role, chunked, feed_chunked , llm, embed):
    # """
    #     chunk document sumber;
    # """
    rag_dic = None
    chunk =  chunked   
    list_key = list(chunk.keys())
    if role not in list_key:
        st.toast("Tidak ada dokumen terkait!")
    else:
        to_chunk = chunk[role]    
        st.toast(f"Your Role : {role}")
        retriever = load_retriever(embed, role, to_chunk )
                
                # """
                #     chunk document feedback
                # """
        retriever_feedback = None
        if feed_chunked is not None and role in feed_chunked:
            to_chunk_feed = feed_chunked[role]
            retriever_feedback = load_retriever_feed(embed, role, to_chunk_feed) 
                #dictionary untuk digunakan di function inference
        rag_dic = {
                        "retriever" : retriever,
                        "retriever_feed": retriever_feedback,
                        "embed" :embed,
                        "llm" : llm
                    }
            
    return rag_dic


