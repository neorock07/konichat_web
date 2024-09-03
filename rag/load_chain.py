from langchain.chains import RetrievalQA
# """
    #     function untuk membuat Retrieval document 
    #     dari vectorstore dengan tingkat similarity 
    #     tertinggi dengan query user.
        
    #     params: 
    #         retriever (VectorStoreRetrivier) :object retriever dari vectorstore sebagai agent yang mencari index berdasarkan kesamaan.
    #         llm (Ollama): model LLM yang dimuat oleh Ollama engine
    #         prompt (str): template prompt untuk pengaturan LLM  
    # """
def load_qa_chain(retriever, llm, prompt):
        return RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            return_source_documents = True,
            chain_type_kwargs={'prompt':prompt}
        )