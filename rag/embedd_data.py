from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.hyde.base import HypotheticalDocumentEmbedder
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.runnables import ConfigurableField, RunnableLambda

# """
#         Kode untuk memuat model Embedding yang akan digunakan untuk 
#         mengubah data hasil chunking/splitting menjadi dimensi embeddings (ruang vector)

#         params:
#             model_path (str): path model encoder embedding
#             normalize_embedding (bool): default True 
#         returns:
#               objek HuggingFaceEmbeddings
# """

def load_embedding_model(model_path, normalize_embedding=True):
        return HuggingFaceEmbeddings(
            model_name=model_path, 
            model_kwargs={'device':'cpu'},
            encode_kwargs = {
                'normalize_embeddings' : normalize_embedding
            }
        )
        
"""
        kode untuk membuat embeddings (vector dari tiap chunk document),
        dan disimpan ke vectorstore FAISS.
        
        params:
            llm: model ChatOllama
            chunks List[document]: document hasil chunk
            embedding_model Embeddings: model yang digunakan untuk melakukan embedding data
            storing_path: lokasi path penyimpanan vectorstore
        returns:
            vectorstore: hasil embeddings berupa data vector documents    
    """    
        
def create_embeddings(llm, chunks, embedding_model, storing_path="vectorstore"):
    
    bm25 = BM25Retriever.from_documents(chunks)
    bm25.k = 10
    
    vector_retriver = FAISS.from_documents(chunks, embedding_model)

    # Menyimpan retriever ke path lokal
    vector_retriver.save_local(storing_path)

"""
        kode untuk membuat embeddings (vector dari tiap chunk text),
        dan disimpan ke vectorstore FAISS.
        
        params:
            llm: model ChatOllama
            chunks List[document]: document hasil chunk
            embedding_model Embeddings: model yang digunakan untuk melakukan embedding data
            storing_path: lokasi path penyimpanan vectorstore
        returns:
            vectorstore: hasil embeddings berupa data vector documents    
    """    


def create_embeddings_by_texts(chunks, embedding_model, storing_path="vectorstore"):
    retriever = FAISS.from_texts(chunks, embedding_model)
    
    bm25 = BM25Retriever.from_texts(chunks)
    bm25.k = 10
    
    # Menyimpan retriever ke path lokal
    retriever.save_local(storing_path)
    

# """
#         kode untuk load objek retriever sesuai dengan role user
        
#         params:
#             embed: model yang digunakan untuk melakukan embedding data
#             role (str) : role user
#             chunks List[document]: document hasil chunk
            
            
#         returns:
#             vectorstore: hasil embeddings berupa data vector documents    
#     """
    

def load_retriever(embed, role, chunks):
    vector_path = f"vectorstore_{role}"
    retriever = {}
    vector_store =  FAISS.load_local(vector_path, embed, allow_dangerous_deserialization=True)
    
    bm25 = BM25Retriever.from_texts(chunks)
    bm25.k = 10
    
     #buat retriever hyde dan vector retriever
    vector_retriver = vector_store.as_retriever(search_type="mmr",
                                                search_kwargs={'k': 15, 
                                                'fetch_k': 30})   
    # wrap retriever sebagai Runnable
    retrievers = [
        RunnableLambda(lambda q: bm25.get_relevant_documents(q)),  
        vector_retriver
    ]
    
    # Membuat Hybrid Search dengan Ensemble kedua metode
    vectorstore = EnsembleRetriever(retrievers=retrievers, weights=[0.3,0.7])
    retriever[role] = vectorstore
    
    return retriever[role]


"""
        kode untuk load objek retriever untuk doc. feedback sesuai dengan role user
        
        params:
            embed: model yang digunakan untuk melakukan embedding data
            role (str) : role user
            chunks List[document]: document hasil chunk 
            
        returns:
            vectorstore: hasil embeddings berupa data vector documents    
    """
 
def load_retriever_feed(embed, role, chunks):
    retriever = {}
    vector_path = f"vectorstore_feedback_{role}"
    vector_store =  FAISS.load_local(vector_path, embed, allow_dangerous_deserialization=True)
    # bm25 = BM25Retriever.from_texts(chunks)
    bm25 = BM25Retriever.from_documents(chunks)
    bm25.k = 1
    
     #buat retriever vector retriever
    vector_retriver = vector_store.as_retriever(
                                    search_type="similarity_score_threshold",
                                    search_kwargs={'score_threshold': 0.99},
                                    )
    
    # wrap retriever sebagai Runnable
    retrievers = [
        RunnableLambda(lambda q: bm25.get_relevant_documents(q)),  
        vector_retriver
    ]
    
    # Membuat Hybrid Search dengan Ensemble kedua metode
    retrieve = EnsembleRetriever(retrievers=retrievers, weights=[0.3,0.7])
    retriever[role] = retrieve
    return retriever[role]

   
    