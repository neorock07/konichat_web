from warnings import deprecated
from langchain.chains import RetrievalQA

@deprecated
def load_qa_chain(retriever, llm, prompt):
    """
    **DO NOT USE THIS FUNCTION, 
    THIS FUNCTION HAS BEEN DEPRECATED AND NOT USED ANYMORE
    IN THIS PROJECT, PREFER TO REMOVE OR RETAIN THIS CODE.
    USE SUGGESTED FUNCTION IN FILE `embedd_data.py` INSTEAD.
    BUT IT PERMITTED TO RE-CONSTRUNCT THE CODE TO USE THIS FUNCTION.**
    
    Function untuk membuat Retrieval document dari vectorstore dengan tingkat similarity 
    tertinggi dengan query user;
    
    Parameters:
        retriever (VectorStoreRetrivier) : object retriever dari vectorstore sebagai agent yang mencari index berdasarkan kesamaan
        llm (ChatOllama) : model llm ChatOllama
        prompt (str) : template prompt untuk pengaturan LLM.
    Returns:
        RetrievalQA.    
        
    """
    
    return RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            return_source_documents = True,
            chain_type_kwargs={'prompt':prompt}
        )