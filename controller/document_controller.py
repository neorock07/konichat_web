from datetime import datetime
from flask import request
import requests
import streamlit as st
from pathlib import Path
import os


def upload_document(file, id_role,):
    # URL endpoint Django untuk upload file
    url = "http://127.0.0.1:8000/api/doc/upload"

    # File dan data lain yang ingin dikirim
    if file is not None:
        file_path = file.getvalue()
        id_role = id_role

        data = {
                'id_role': id_role, 
                'title' : file.name,
                  
        }

            # Kirim POST request dengan file dan data
        response = requests.post(
            url,
            data=data,
            files={"file" : (file.name, file_path, 'application/pdf')}
            )
        
        # Cek status dan response
        if response.status_code == 201:
            print("File berhasil diupload!")
            print(response.json())
            st.toast("✅ File upload success!")
            return response.json()
        elif response.status_code == 200:
            st.toast("✅ File updated success!")
            return response.json()
        else:
            print(f"Gagal upload file. Status code: {response.status_code}")
            print(response.text)
            st.toast("❌ File upload failed!")
            return response.json()      
    else:
        return "file is None"      

def update_document(file, id_role, tanggal):
    # URL endpoint Django untuk upload file
    url = f"http://127.0.0.1:8000/api/doc/update/{id_role}"

    # File dan data lain yang ingin dikirim
    if file is not None:
        file_path = file.getvalue()
        id_role = id_role

        data = {
                'title' : file.name,
                'tanggal' : tanggal  
              }

            # Kirim POST request dengan file dan data
        response = requests.patch(
            url,
            data=data,
            files={"file" : (file.name, file_path, 'application/pdf')}
            )
        
        # Cek status dan response
        if response.status_code == 200:
            st.toast("✅ File updated success!")
            return response.json()
        else:
            print(f"Gagal upload file. Status code: {response.status_code}")
            # print(response.text)
            st.toast("❌ failed update file!")
            return response.json()      
    else:
        return "file is None"      
    
def get_all_docs():    
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/doc/'
        
    try:
        # Melakukan POST request ke endpoint
        response = requests.get(url)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 200:
                # Mengambil respons JSON
                # st.toast("✔️ Got Docs")
                return response.json()
        else:
                # st.toast("❌ Couldn't get Docs")
                return "error"    
    except Exception as e:
                return f"error | {e}"  

# """
#     kode utuk mendapatkan dokumen by id_role user;
# """
def get_by_id_docs(id_role):    
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/doc/id'
    data = {
                'id_role' : id_role
            }    
    try:
        # Melakukan POST request ke endpoint
        response = requests.get(url, data=data)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 200:
                # Mengambil respons JSON
                st.toast("✔️ Got Docs")
                return response.json()
        else:
                st.toast("❌ Couldn't get Docs")
                return "error"    
    except Exception as e:
                st.toast("❌ Couldn't get Docs | try refresh page!")
                st.warning(f"Message : {e}")
                st.stop()
                  

# """
#     kode utuk mendapatkan all dokumen feedback;
# """
def get_feedback_doc():    
    # URL endpoint 
    url = 'http://127.0.0.1:8000/api/feedback/doc/'
 
    try:
        # Melakukan POST request ke endpoint
        response = requests.get(url)
            
         # Memeriksa apakah request berhasil
        if response.status_code == 200:
                # Mengambil respons JSON
                return response.json()
        else:
                st.toast("❌ Couldn't get Fallback")
                return "error"    
    except Exception as e:
                st.toast("❌ Couldn't get Docs | try refresh page!")
                st.warning(f"Message : {e}")
                st.stop()
                
# """
#     fungsi untuk upload dokumen, 
#     dapat bekerja baik dengan insert atau update;
#     jika dokumen pada n_role not exist maka insert, 
#     jika sudah ada maka update;
# """

def upload_document_feedback(file, id_role,):
    # URL endpoint Django untuk upload file
    url = "http://127.0.0.1:8000/api/feedback/doc/upload"

    # File dan data lain yang ingin dikirim
    if file is not None:
        file_path = file.getvalue()
        id_role = id_role

        data = {
                'id_role': id_role, 
                'title' : file.name,
                'tanggal' : datetime.today().strftime('%Y-%m-%d')
                  
        }

            # Kirim POST request dengan file dan data
        response = requests.post(
            url,
            data=data,
            files={"file" : (file.name, file_path, 'application/pdf')}
            )
        
        # Cek status dan response
        if response.status_code == 201:
            print("File berhasil diupload!")
            print(response.json())
            st.toast("✅ File upload success!")
            return response.json()
        elif response.status_code == 200:
            st.toast("✅ File updated success!")
            return response.json()
        else:
            print(f"Gagal upload file. Status code: {response.status_code}")
            print(response.text)
            st.toast("❌ File upload failed!")
            return response.json()      
    else:
        return "file is None"      
                
            
def download_doc(url, file_name):
    response = requests.get(url)
    file_path = Path(file_name)
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return file_path
        
                
            
            
            
              