from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.hyde.base import HypotheticalDocumentEmbedder
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.runnables import ConfigurableField, RunnableLambda

 # """
    #     Kode untuk memuat model Embedding yang akan digunakan untuk 
    #     mengubah data hasil chunking/splitting menjadi dimensi embeddings (ruang vector)

    #     params:
    #         model_path (str): path model encoder embedding
    #         normalize_embedding (bool): default True 
    #     returns:
    #           objek HuggingFaceEmbeddings
    # """

def load_embedding_model(model_path, normalize_embedding=True):
        return HuggingFaceEmbeddings(
            model_name=model_path, 
            model_kwargs={'device':'cpu'},
            encode_kwargs = {
                'normalize_embeddings' : normalize_embedding
            }
        )
        
 # """
    #     kode untuk membuat embeddings (vector dari tiap chunk document),
    #     dan disimpan ke vectorstore FAISS.
        
    #     params:
    #         chunks List[document]: document hasil chunk
    #         embedding_model Embeddings: model yang digunakan untuk melakukan embedding data
    #         storing_path: lokasi path penyimpanan vectorstore
    #     returns:
    #         vectorstore: hasil embeddings berupa data vector documents    
    # """    
        
def create_embeddings(llm, chunks, embedding_model, storing_path="vectorstore"):
    hyde = HypotheticalDocumentEmbedder.from_llm(llm=llm, base_embeddings=embedding_model, prompt_key="web_search")
    hyde_retriever = FAISS.from_documents(chunks, hyde)
    
    bm25 = BM25Retriever.from_documents(chunks)
    bm25.k = 10
    
    vector_retriver = FAISS.from_documents(chunks, embedding_model)

    # Menyimpan retriever ke path lokal
    hyde_retriever.save_local(storing_path)
    
    # #buat retriever hyde dan vector retriever
    # vector_retriver = vector_retriver.as_retriever(search_kwargs={"k": 10})
    # hyde_retriever = hyde_retriever.as_retriever(search_kwargs={"k": 10})
    
    # # wrap retriever sebagai Runnable
    # retrievers = [
    #     # RunnableLambda(lambda q: hyde_retriever.get_relevant_documents(q)),  
    #     RunnableLambda(lambda q: bm25.get_relevant_documents(q)),  
    #     vector_retriver
    # ]
    
    # # Membuat Hybrid Search dengan Ensemble kedua metode
    # vectorstore = EnsembleRetriever(retrievers=retrievers, weights=[0.3,0.7])
    
    # return vectorstore   
    
    
def load_retriever(embed, role, chunks, llm):
    vector_path = f"vectorstore_{role}"
    retriever = {}
    vector_store =  FAISS.load_local(vector_path, embed, allow_dangerous_deserialization=True)
    hyde = HypotheticalDocumentEmbedder.from_llm(llm=llm, base_embeddings=embed, prompt_key="web_search")
    hyde_retriever = FAISS.from_documents(chunks, hyde)
    
    bm25 = BM25Retriever.from_documents(chunks)
    bm25.k = 5
    
    # vector_retriver = FAISS.from_documents(chunks, embed)
     #buat retriever hyde dan vector retriever
    vector_retriver = vector_store.as_retriever(search_kwargs={"k": 5})
    # vector_retriver = vector_retriver.as_retriever(search_kwargs={"k": 10})
    hyde_retriever = hyde_retriever.as_retriever(search_kwargs={"k": 5})
    
    # wrap retriever sebagai Runnable
    retrievers = [
        # RunnableLambda(lambda q: hyde_retriever.get_relevant_documents(q)),  
        RunnableLambda(lambda q: bm25.get_relevant_documents(q)),  
        vector_retriver
    ]
    
    # Membuat Hybrid Search dengan Ensemble kedua metode
    vectorstore = EnsembleRetriever(retrievers=retrievers, weights=[0.3,0.7])
    retriever[role] = vectorstore
    
    return retriever[role]   
    