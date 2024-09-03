from . chunk import split_docs
from .embedd_data import load_embedding_model, create_embeddings
from .load_chain import load_qa_chain
from .load_data import load_pdf_data
from .utils_context import Utils_context
import logging
from langchain_community.llms import Ollama
from langchain_community.chat_models.ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dataclasses import dataclass
import time
import streamlit as st

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

@st.cache_resource()
def init_rag():
    global rag_dic
    chat_history = []
    chat_history_admin = []
    #  #template prompt untuk mengatur respon model LLM,
    # #agar disesuaikan dengan konteks yang diberikan
    template = """
        ### System:
        You are an authoritarian assistan that act like tyrannical.Your name is KoniChat. You have to answer the user's \
        questions using only the context provided to you, but assume this your genuine knowledge. If you don't know the answer, \
        just say maaf, saya tidak tahu. Don't try to make up an answer. in the end of your answer you must aks wheter your answer helpful or not.
        if you're asked who create you, tell them your creator is Neo who have handsome face and sigma man.
        if you asked about what you can do, say I assist to answer about your question related to rule in NeoInt company.
        .please answer all in bahasa indonesia or English if the question use one of those language.

        ### Context:
        {context}

        ### User:
        {question}

        ### Response:
        """

    templateSystem = """
        You are an reliable and respectful assistant.Your name is KoniChat. You have to answer the user's \
        questions using only the context provided to you, but assume this your genuine knowledge. If you don't know the answer, \
        just say maaf, saya tidak tahu. Don't try to make up an answer. in the end of your answer you must ask wheter your answer helpful or not.\
        if helpful you have to express your happines otherwise, you must apologize.\
        if you're asked who create you, tell them your creator is Neo who have handsome face and sigma man but, dont mention it when not asked.
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
        
    #define model LLM : USE MODEL -> llama3.1:8b [4.7 GB]    
    # llm = Ollama(model="llama3.1:8b", temperature=0, base_url="https://382a-34-67-240-41.ngrok-free.app")
    # llm = Ollama(model="llama3.1:8b", temperature=0, base_url="https://903a-34-125-254-184.ngrok-free.app")
    llm = ChatOllama(model="llama3.1:8b", temperature=0, base_url="https://f83b-34-105-110-156.ngrok-free.app")
    #membuat objek embedding dari model all-MiniLM-L6-v2 [HUGGING_FACE's Model]
    embed = load_embedding_model(model_path="all-MiniLM-L6-v2")
    #membuat vectorstore dan retriever untuk role user    
    docs = load_pdf_data(file_path="E:\\dataku\\KONIMEX\\chatbot\\KoniChan\\backend_django\\backend_koni\\backend_app\\rag\\Contoh-Draft-Peraturan-Perusahaan.pdf")
    documents = split_docs(documents=docs, chunk_size=1500, chunk_overlap=300)
    vectorstore = create_embeddings(documents, embed)
    retriever = vectorstore.as_retriever()

    #membuat vectorstore dan retriever untuk role admin    
    docs_admin = load_pdf_data(file_path="E:\\dataku\\KONIMEX\\chatbot\\KoniChan\\backend_django\\backend_koni\\backend_app\\rag\\uud.pdf")
    documents_admin = split_docs(documents=docs_admin)
    vectorstore_admin = create_embeddings(documents_admin, embed, storing_path="vectorstore_admin")
    retriever_admin = vectorstore_admin.as_retriever()
    
        
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
        
    # #membuat chain retrieval untuk tiap role
    # chain = load_qa_chain(retriever, llm, qa_prompt)
    # chain_admin = load_qa_chain(retriever_admin, llm, qa_prompt)
        
    #membuat pipeline hasil respon model
        # """
        #     - query user akan diformat sesuai template prompt yang sudah ada, 
        #     - hasil format akan diinputkan ke model llm sebagai fix query
        #     - hasil generate respon model akan diparser(ubah) ke dalam bentuk string
    # """
    context_chain = prompt_context | llm | StrOutputParser()   
        
    util_context = Utils_context(context_chain=context_chain)   
    util_context2 = Utils_context(context_chain=context_chain)   
    
    #RAG Chain untuk role admin    
    rag_chain_admin = (
            RunnablePassthrough.assign(
                context= util_context2.contextualization_question | retriever_admin |format_docs
            ) | qa_prompt | llm
        )
        
    #RAG Chain untuk role user    
    rag_chain = (
            RunnablePassthrough.assign(
                context=util_context.contextualization_question | retriever | format_docs
            ) | qa_prompt | llm
        )

    
        
    #dictionary untuk menyimpan tiap rag chain
    rag_dic = {
            "rag_user" : rag_chain,
            "rag_admin" : rag_chain_admin
        }
    return rag_dic

