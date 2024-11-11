from langchain_community.document_loaders import PyMuPDFLoader
import streamlit as st 
 
@st.cache_data
def load_pdf_data(file_path):
        """
        kode untuk load pdf data
        Parameters:
            file_path (str): argument diisi dengan lokasi file pdf
        Returns:
            docs (List[document]): objek loaded yang sudah termuat      
        """
        loader = PyMuPDFLoader(file_path=file_path)
        docs = loader.load()
        return docs