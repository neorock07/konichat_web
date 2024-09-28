from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import SpacyTextSplitter
import streamlit as st
# """
    #     kode untuk chunk (memotong dokumen menjadi bagian-bagian yang lebih kecil)
    #     params:
    #         documents (List[document]): argument diisi dengan document yang sudah dimuat
    #         chunk_size (int) : size pembagian data
    #         chunk_overlap (int): besar data yang diskip (per-kata)
    #     returns:
    #         chunks (List[document]): objek hasil split dokumen    
    # """

def split_docs(_documents, _chunk_size, _chunk_overlap):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=_chunk_size, 
            chunk_overlap=_chunk_overlap
        )
        chunks = text_splitter.split_documents(documents=_documents)
        return chunks