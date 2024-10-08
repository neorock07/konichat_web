from pydoc import doc
from networkx import group_degree_centrality
from . chunk import split_docs
from .embedd_data import load_embedding_model, create_embeddings, load_retriever
from .load_data import load_pdf_data
from .utils_context import Utils_context
import logging
from langchain_community.llms import Ollama
from langchain_community.chat_models.ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.retrievers.document_compressors import FlashrankRerank
from langchain.retrievers import ContextualCompressionRetriever
from dataclasses import dataclass
import time
import streamlit as st
from controller.document_controller import download_doc, get_all_docs, get_by_id_docs
from langchain_core.documents.base import Document
from langchain.callbacks.base import BaseCallbackHandler

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
# @st.cache_data
def load_downloaded_file():
    global file_path_manager
    global file_path_user
    docs_all = get_all_docs()
    path_docs_dict = []
    role_set = []
    for i in docs_all:
        path_docs_dict.append(download_doc(i['file'], i['title']))  
        role_set.append(i['name'])
    return path_docs_dict, role_set


# """
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
    doc_chunked: dict[int, list[Document]] = {}
    doc_path, roles = load_downloaded_file()
    roles = list(roles)
    
    # Mengelompokkan dokumen berdasarkan role
    group_doc = {}
    for i in range(len(doc_path)):
        if roles[i] not in group_doc:
            group_doc[roles[i]] = []
        group_doc[roles[i]].append(doc_path[i])      
    
    # Membagi dokumen menjadi chunk dan menyimpannya di doc_chunked
    for i in group_doc:
        documents: list[Document] = []
        for j in group_doc[i]:
            docs = load_pdf_data(file_path=j)
            documents.extend(split_docs(_documents=docs, _chunk_size=1000, _chunk_overlap=200))  
        if i not in doc_chunked:
            doc_chunked[i] = []
        
        # Menggunakan extend agar tidak membuat list di dalam list
        doc_chunked[i].extend(documents)
    
    # Membuat embeddings untuk setiap dokumen yang sudah di-chunk
    for i in doc_chunked:
        create_embeddings(_llm, doc_chunked[i], _embed, storing_path=f"vectorstore_{i}")

    return doc_chunked    

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
    llm = ChatOllama(model="qwen2.5", 
                     temperature=0,
                     base_url="https://f779-35-222-81-176.ngrok-free.app")
    
    # membuat objek embedding dari model all-MiniLM-L6-v2 [HUGGING_FACE's Model]
    embed = load_embedding_model(model_path="all-MiniLM-L6-v2")
    logger.debug("download embedding finished") 
    
    #paggil fungsi ini untuk melakukan proses embedding
    chunked = chunked_doc(embed, llm)
    
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
# """
  
def invoke_rag(role, chunked, context_question, qa_prompt, llm, embed):
    chunk =  chunked
    to_chunk = chunk[role]
    st.toast(f"Your Role : {role}")
    retriever = load_retriever(embed, role, to_chunk, llm )
        
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
            "prompt" : rag_chain.get_prompts(),
            "embed" :embed,
            "llm" : llm
        }
    return rag_dic


