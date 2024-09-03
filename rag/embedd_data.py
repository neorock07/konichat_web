from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


 # """
    #     Kode untuk memuat model Embedding yang akan digunakan untuk 
    #     mengubah data hasil chunking/splitting menjadi dimensi embeddings (ruang vector)

    #     params:
    #         model_path: 
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
        
def create_embeddings(chunks, embedding_model, storing_path="vectorstore"):
        vectorstore = FAISS.from_documents(chunks, embedding_model)
        vectorstore.save_local(storing_path)
        print(vectorstore)
        return vectorstore        