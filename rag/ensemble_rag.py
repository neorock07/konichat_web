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
    # file_path_manager = download_doc(docs_manager['file'], docs_manager['title'])
    # file_path_user = download_doc(docs_user['file'], docs_user['title'])
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

        
    # logger.debug(f"group_doc_chunked : \n {group_doc}")
    #membuat vectorstore dan retriever    
    # for i in range(len(doc_path)):     
    #     docs = load_pdf_data(file_path=doc_path[i])
    #     documents = split_docs(_documents=docs, _chunk_size=1000, _chunk_overlap=200) 
    #     doc_chunked[roles[i]] = documents
    #     create_embeddings(_llm, documents, _embed, storing_path=f"vectorstore_{roles[i]}")
    # logger.debug(f"len doc_path : \n {doc_path}")
    # logger.debug(f"roles : {roles}")
    return doc_chunked    

# """
#     function untuk memproses embedding document;
# """
# @st.cache_data
# def process_embedding(_embed, _llm, _chunked):
#     # doc_path = load_downloaded_file_byId(role)
#     # doc_path, roles = load_downloaded_file()
#     chunk_dokumen = _chunked
#     for i in chunk_dokumen:
#         create_embeddings(_llm, chunk_dokumen[i], _embed, storing_path=f"vectorstore_{i}")
    #membuat vectorstore dan retriever    
    # for i in range(doc_path):     
    #     docs = load_pdf_data(file_path=doc_path[i])
    #     documents = split_docs(documents=docs, chunk_size=1000, chunk_overlap=100)
    #     retriever = create_embeddings(llm, documents, embed, storing_path=f"vectorstore_{roles[i]}")
    
    # return retriever


@st.cache_data
def init_rag():
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
    
    
    llm = ChatOllama(model="gemma2:9b", temperature=0, base_url="https://a829-34-168-153-254.ngrok-free.app")
    # llm = ChatOllama(model="llama3.1:8b", temperature=0, base_url="https://569f-34-70-156-78.ngrok-free.app")
    
    # membuat objek embedding dari model all-MiniLM-L6-v2 [HUGGING_FACE's Model]
    # embed = load_embedding_model(model_path="paraphrase-multilingual-MiniLM-L12-v2")
    embed = load_embedding_model(model_path="all-MiniLM-L6-v2")
    logger.debug("download embedding finished") 
    #membuat retriever
    chunked = chunked_doc(embed, llm)
    # retriever = process_embedding(embed, llm, chunked_doc)
    # #re-rank document 
    # compressor = FlashrankRerank()
    # compression_retriever = ContextualCompressionRetriever(
    #     base_compressor=compressor,
    #     base_retriever=retriever
    # )
    
    # st.toast("✅ embedding selesai")    
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
    
    # chunk =  chunked_doc
    # to_chunk = chunk[role]
    # retriever = load_retriever(embed, role, to_chunk, llm )
        
    # rag_chain = (
    #         RunnablePassthrough.assign(
    #             context=util_context.contextualization_question | RunnableLambda(lambda question: retriever.invoke(
    #         question, config={"configurable": {"search_kwargs_faiss": {"k": 5}}}
    #     )) | format_docs
    #         ) | qa_prompt | llm
    #     )
    
    # rag_dic = {
    #         "rag_user" : rag_chain,
    #         "retriever" : retriever,
    #         "prompt" : rag_chain.get_prompts(),
    #         "embed" :embed
    #     }
    # return rag_dic
    return {
        "util_context" : util_context.contextualization_question, 
        "qa_prompt" : qa_prompt, 
        "llm" : llm,
        "chunked" : chunked, 
        "embed" : embed
    }
    
    # rag_chain = (
    #         RunnablePassthrough.assign(
    #             context=util_context.contextualization_question |  RunnableLambda(lambda question: retriever.invoke(
    #         question, config={"configurable": {"search_kwargs_faiss": {"k": 5}}}
    #     )) | format_docs
    #         ) | qa_prompt | llm
    #     )
    
        
    # #dictionary untuk digunakan di function inference
    # rag_dic = {
    #         "rag_user" : rag_chain,
    #         "retriever" : retriever,
    #         "prompt" : rag_chain.get_prompts(),
    #         "embed" :embed
    #     }
    # return rag_dic
# @st.cache_data
def invoke_rag(role, chunked, context_question, qa_prompt, llm, embed):
    chunk =  chunked
    to_chunk = chunk[role]
    st.toast(f"role : {role}")
    # st.info(f"{len(chunk)}\n{to_chunk}")
    # st.info(f"chunked : \n {chunked}\nto_chunk : \n{to_chunk}")
    retriever = load_retriever(embed, role, to_chunk, llm )
        
    rag_chain = (
            RunnablePassthrough.assign(
                context=context_question | RunnableLambda(lambda question: retriever.invoke(
            question, config={"configurable": {"search_kwargs_faiss": {"k": 3}}}
        )) | format_docs
            ) | qa_prompt | llm
        )
    
        
    #dictionary untuk digunakan di function inference
    rag_dic = {
            "rag_user" : rag_chain,
            "retriever" : retriever,
            "prompt" : rag_chain.get_prompts(),
            "embed" :embed
        }
    return rag_dic


