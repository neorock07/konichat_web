from . chunk import split_docs
from .embedd_data import load_embedding_model, create_embeddings
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

# Mengatur konfigurasi logging
logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

rag_dic = None
file_path_manager = None
file_path_user = None

# """
#     mengambil seluruh data dokumen;
#     tujuan : `mengambil data semua lalu process satu waktu`
#     cons : `time consume terlalu banyak`
# """
def load_downloaded_file():
    global file_path_manager
    global file_path_user
    docs_all = get_all_docs()
    docs_manager = docs_all[0]
    docs_user = docs_all[1]
    
    file_path_manager = download_doc(docs_manager['file'], docs_manager['title'])
    file_path_user = download_doc(docs_user['file'], docs_user['title'])
    return file_path_manager, file_path_user


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
#     function untuk memproses embedding document;
# """
def process_embedding(role, embed, llm):
    doc_path = load_downloaded_file_byId(role)
    #membuat vectorstore dan retriever    
    docs = load_pdf_data(file_path=doc_path)
    # docs = load_pdf_data(file_path="E:\\dataku\\KONIMEX\\chatbot\\KoniChan\\web\\rag\\Contoh-Draft-Peraturan-Perusahaan.pdf")
    documents = split_docs(documents=docs, chunk_size=1000, chunk_overlap=100)
    retriever = create_embeddings(llm, documents, embed)
    # retriever = vectorstore.as_retriever( 
    #     search_type="similarity",
    #     search_kwargs={'k': 5})
    
    return retriever

# @st.cache_data
def init_rag(role:str):
    global rag_dic
    config = {"configurable" : {
            "search_kwargs_faiss": {"k": 1}
        }}
     
    templateSystem = """
        ### Instruction
        You are an reliable and respectful assistant.Your name is KoniChat. You have to answer the user's \
        questions using only the context provided to you, but assume this your genuine knowledge. If you don't know the answer, \
        just say maaf, saya tidak tahu. Don't try to make up an answer. in the end of your answer you must ask wheter your answer helpful or not.\
        if helpful you have to express your happines otherwise, you must apologize.\
        if you asked about what you can do, say I assist to answer about your question related to rule in Konimex company.
        .please answer all in bahasa indonesia or English if the question use one of those language with Empathetic response.

        ### Context:
        {context}

        """


    templateContext = """
        Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history.\
        just reformulate it if needed otherwise return it as you have answer it.
        """
    
    
    llm = ChatOllama(model="gemma2:9b", temperature=0, base_url="https://0d0a-34-16-76-80.ngrok-free.app")
    # llm = ChatOllama(model="llama3.1:8b", temperature=0, base_url="https://569f-34-70-156-78.ngrok-free.app")
    
    # membuat objek embedding dari model all-MiniLM-L6-v2 [HUGGING_FACE's Model]
    # embed = load_embedding_model(model_path="paraphrase-multilingual-MiniLM-L12-v2")
    embed = load_embedding_model(model_path="all-MiniLM-L6-v2")
    logger.debug("download embedding finished") 
    #membuat retriever
    retriever = process_embedding(role, embed, llm)
    # #re-rank document 
    # compressor = FlashrankRerank()
    # compression_retriever = ContextualCompressionRetriever(
    #     base_compressor=compressor,
    #     base_retriever=retriever
    # )
    
    st.toast("✅ embedding selesai")    
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
        
 
    #membuat pipeline hasil respon model
        # """
        #     - query user akan diformat sesuai template prompt yang sudah ada, 
        #     - hasil format akan diinputkan ke model llm sebagai formatted query
        #     - hasil generate respon model akan diparser(ubah) ke dalam bentuk string
    # """
    context_chain = prompt_context | llm | StrOutputParser()   
    
    #buat objek untuk contextualization     
    util_context = Utils_context(context_chain=context_chain)   
    
    
    rag_chain = (
            RunnablePassthrough.assign(
                context=util_context.contextualization_question |  RunnableLambda(lambda question: retriever.invoke(
            question, config={"configurable": {"search_kwargs_faiss": {"k": 5}}}
        )) | format_docs
            ) | qa_prompt | llm
        )
    
    # logger.debug("QA PROMPT : " + str(qa_prompt.messages))
        
    #dictionary untuk digunakan di function inference
    rag_dic = {
            "rag_user" : rag_chain,
            "retriever" : retriever,
            "prompt" : rag_chain.get_prompts(),
            "embed" :embed
        }
    return rag_dic

def invoke_rag():
    pass

