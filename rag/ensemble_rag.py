from . chunk import split_docs, EOSSplitter
from .embedd_data import create_embeddings_by_texts, load_embedding_model, create_embeddings, load_retriever, load_retriever_feed
from .load_data import load_pdf_data
from .utils_context import Utils_context
import logging
from langchain_community.chat_models.ollama import ChatOllama
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

# @st.cache_data
# def chunked_doc(_embed, _llm,):
#     full_pdf = ""
#     pdfs = None
#     chunk_eos = EOSSplitter(chunk_size=1200, chunk_overlap=300)
#     # """
#     #     kode untuk memproses chunk sumber documents
#     # """
#     doc_chunked: dict[int, list[Document]] = {}
#     doc_path, roles, doc_feedback_path = load_downloaded_file()
#     roles = list(roles)
    
#     # Mengelompokkan dokumen berdasarkan role
#     group_doc = {}
#     for i in range(len(doc_path)):
#         if roles[i] not in group_doc:
#             group_doc[roles[i]] = []
#         group_doc[roles[i]].append(doc_path[i])      
    
#     # Membagi dokumen menjadi chunk dan menyimpannya di doc_chunked
#     for i in group_doc:
#         documents: list[Document] = []
#         for j in group_doc[i]:
#             docs = load_pdf_data(file_path=j)
#             ##############################################
#             #              troubleshoot                  #
#             ##############################################
#             # for g in docs:
#             #     full_pdf += g.page_content
#             # pdfs = full_pdf.split("<EOS>")
#             # for mj in pdfs:
#             #     logger.debug(mj+"\n\n")
            
#             documents.extend(chunk_eos.split_documents(documents=docs))  
#             # documents.extend(split_docs(_documents=docs, _chunk_size=1000, _chunk_overlap=200))  
#         if i not in doc_chunked:
#             doc_chunked[i] = []
        
#         # Menggunakan extend agar tidak membuat list di dalam list
#         doc_chunked[i].extend(documents)
    
#     # Membuat embeddings untuk setiap dokumen yang sudah di-chunk
#     for i in doc_chunked:
#         create_embeddings(_llm, doc_chunked[i], _embed, storing_path=f"vectorstore_{i}")
    
#     ############################################################
#     #               Chunk Document Feedback                   #
#     ##########################################################
    
#     dict_feed:dict[str, list[Document]] = {}
#     if doc_feedback_path is not [] or doc_feedback_path is not None:
#         # Membuat chunk untuk document feedback
#         for i in doc_feedback_path:
#             doc_feed = load_pdf_data(file_path = i['path'])
#             feed_chunked = split_docs(_documents = doc_feed, _chunk_size=1500, _chunk_overlap=400, separator=["<EOS>"])
#             dict_feed[i['role_name']] = feed_chunked
#             # membuat embedding untuk dokumen revisi feedback
#             create_embeddings(_llm, feed_chunked, _embed, storing_path=f"vectorstore_feedback_{i['role_name']}")    
            
#     return doc_chunked, dict_feed   


 
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
            #              troubleshoot                  #
            ##############################################
            for g in docs:
                full_pdf += g.page_content
            pdfs = full_pdf.split("<EOS>")
            for mj in pdfs:
                list_pdf_content.append(mj)
                # logger.debug(mj+"\n\n")
            
            documents.extend(list_pdf_content)  
            # documents.extend(split_docs(_documents=docs, _chunk_size=1000, _chunk_overlap=200))  
        if i not in doc_chunked:
            doc_chunked[i] = []
        
        # Menggunakan extend agar tidak membuat list di dalam list
        doc_chunked[i].extend(documents)
    
    # Membuat embeddings untuk setiap dokumen yang sudah di-chunk
    for i in doc_chunked:
        # create_embeddings(_llm, doc_chunked[i], _embed, storing_path=f"vectorstore_{i}")
        create_embeddings_by_texts(doc_chunked[i], _embed, storing_path=f"vectorstore_{i}")
    ############################################################
    #               Chunk Document Feedback                   #
    ##########################################################
    
    dict_feed:dict[str, list[Document]] = {}
    if doc_feedback_path is not [] or doc_feedback_path is not None:
        # Membuat chunk untuk document feedback
        for i in doc_feedback_path:
            doc_feed = load_pdf_data(file_path = i['path'])
            feed_chunked = split_docs(_documents = doc_feed, _chunk_size=1500, _chunk_overlap=400, separator=["<EOS>"])
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
     
    templateSystem = """
        ### Instruction
        Anda adalah asisten yang dapat diandalkan dan penuh hormat. Nama Anda KoniChat. Anda harus menjawab \
        pertanyaan hanya menggunakan konteks yang diberikan kepada Anda, tetapi asumsikan ini adalah pengetahuan asli Anda. Jika Anda tidak tahu jawabannya, \
        katakan saja maaf, saya tidak tahu. Jangan mencoba mengarang jawaban. di akhir jawabanmu, kamu harus bertanya apakah jawabanmu bermanfaat atau tidak.\
        jika membantu kamu harus mengungkapkan kebahagiaanmu, sebaliknya kamu harus meminta maaf.\
        jika anda bertanya tentang apa yang dapat anda lakukan, katakanlah saya membantu menjawab pertanyaan anda terkait dengan peraturan di perusahaan Konimex.
        .mohon dijawab semua dalam bahasa indonesia atau bahasa inggris jika pertanyaan menggunakan salah satu bahasa tersebut dengan respon Empati.

        ### Context:
        {context}
        """


    templateContext = """
        Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history.\
        just reformulate it if needed otherwise return it as you have answer it.
        """
    
    
    # llm = ChatOllama(model="gemma2:9b", temperature=0, base_url="https://32b0-34-71-195-79.ngrok-free.app")
    # llm = ChatOllama(model="gemma2:9b", 
    llm = ChatOllama(model="qwen2.5:14b", 
                     temperature=0,
                     base_url="https://4ba5-35-185-174-38.ngrok-free.app")
    
    # membuat objek embedding dari model all-MiniLM-L6-v2 [HUGGING_FACE's Model]
    embed = load_embedding_model(model_path="all-MiniLM-L6-v2")
    logger.debug("download embedding finished") 
    
    #paggil fungsi ini untuk melakukan proses embedding
    # note: default value feed_chunked = {}
    chunked, feed_chunked = chunked_doc(embed, llm)
    
    if feed_chunked is {}:
        feed_chunked = None
    #[OPTIONAL RE-RANK MAYBE FOR FUTURE USE]
    # #re-rank document 
    # compressor = FlashrankRerank()
    # compression_retriever = ContextualCompressionRetriever(
    #     base_compressor=compressor,
    #     base_retriever=retriever
    # )
        
    #membuat template prompt untuk memberi tahu bahwa terdapat probabilitas 
    #percakapan sebelumnya relevan untuk menjawab pertanyaan terkini (give context for model)
    prompt_context = ChatPromptTemplate.from_messages(
            [
                ("system", templateContext),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )
    #template prompt untuk formatting query user sebelum di inputkan ke model 
    qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", templateSystem),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )
        
     
    context_chain = prompt_context | llm | StrOutputParser()     
    #buat objek untuk contextualization     
    util_context = Utils_context(context_chain=context_chain)   
    
    return {
        "util_context" : util_context.contextualization_question, 
        "qa_prompt" : qa_prompt, 
        "llm" : llm,
        "chunked" : chunked,
        "feedback" : feed_chunked, 
        "embed" : embed
    }
    
# """
#     fungsi untuk mendapatkan prediction words dari model LLM;
#     params:
#         role (str) : role user
#         chunked (dict(list, Lit[Document])): dictionary hasil split document masing2 role;
#         context_question : objek sebagai pengarah pemberian context chat history;
#         qa_prompt: template prompt untuk memodifikasi pertanyaan user;
#         llm: model llm ChatOllama
#         embed : model embedding
#     returns:
#         rag_dic (dict)    
#
##   NOTE: kode digunakan di file app.py
# """
  
def invoke_rag(role, chunked, feed_chunked , context_question, qa_prompt, llm, embed):
    # """
    #     chunk document sumber;
    # """
    chunk =  chunked
    to_chunk = chunk[role]
    st.toast(f"Your Role : {role}")
    retriever = load_retriever(embed, role, to_chunk, llm )
    
    # """
    #     chunk document feedback
    # """
    retriever_feedback = None
    if feed_chunked is not None and role in feed_chunked:
        to_chunk_feed = feed_chunked[role]
        retriever_feedback = load_retriever_feed(embed, role, to_chunk_feed) 
    #membuat pipeline hasil respon model
        # """
        #     - query user akan diformat sesuai template prompt yang sudah ada, 
        #     - hasil format akan diinputkan ke model llm sebagai formatted query
        #     - hasil generate respon model akan diparser(ubah) ke dalam bentuk string
    # """
    rag_chain = (
    RunnablePassthrough.assign(
        context=context_question | 
        RunnableLambda(lambda question: retriever.invoke(
            question, config={"configurable": {"search_kwargs_faiss": {"k": 3}}}
        )) | format_docs
    ) | qa_prompt | RunnableLambda(lambda context: generate_stream_tokens(llm, context))
    )
        
    #dictionary untuk digunakan di function inference
    rag_dic = {
            "rag_user" : rag_chain,
            "retriever" : retriever,
            "retriever_feed": retriever_feedback,
            "prompt" : rag_chain.get_prompts(),
            "embed" :embed,
            "llm" : llm
        }
    return rag_dic


