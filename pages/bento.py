import streamlit as st
import time
import requests

def get_all_docs():    
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/doc/'
        
    try:
        # Melakukan POST request ke endpoint
        response = requests.get(url)
            
        # Memeriksa apakah request berhasil
        if response.status_code == 200:
            return response.json()
        else:
            return "error"    
    except Exception as e:
        return f"error | {e}"  


@st.cache_data
def load_downloaded_file():
    docs_all = get_all_docs()
    path_docs_dict = []
    role_set = set()
    for i in docs_all:
        path_docs_dict.append(i['title'])  
        role_set.add(i['name'])
    return path_docs_dict, role_set

@st.cache_data
def coba_split(llm):
    moral = []
    for i in range(1, 5):
        moral.append(i)
        time.sleep(2)
    return moral

@st.cache_data
def coba_chunk():
    a = load_downloaded_file()
    b = coba_split(a)
    return a


def coba_init():
    a = coba_chunk()
    return a


# Pindahkan st.info() ke luar fungsi yang dicache
docs_info = coba_chunk()
if docs_info != "error":
    st.info(docs_info)
else:
    st.error("Failed to load documents")
