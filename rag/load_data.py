from langchain_community.document_loaders import PyMuPDFLoader
 
 # """
    #  kode untuk load pdf data
    #  params:
    #     file_path (str): argument diisi dengan lokasi file pdf
    #  returns:
    #     docs (List[document]): objek loaded yang sudah termuat      
    # """
def load_pdf_data(file_path):
        loader = PyMuPDFLoader(file_path=file_path)
        docs = loader.load()
        return docs