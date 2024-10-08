import streamlit as st
from controller.document_controller import upload_document
from controller.document_controller import update_document
from controller.auth_controller import get_all_role
from controller.feedback_method import get_count_feedback
from controller.document_controller import get_all_docs
from datetime import datetime
import uuid
from annotated_text import annotated_text
import logging
import functools

st.set_page_config("KoniChat | Admin", page_icon="assets/fav.png")

st.header("Admin Dashboard KoniChat")

role = get_all_role()
data_count_feedback = get_count_feedback()
data_docs = get_all_docs()
list_role = []
id_role_selected = None
for i in role:
    list_role.append(i['name'])
if role != "error" or role is not None:
    with st.sidebar:
        st.header("Upload New Doc.")
        st.warning("Upload dokumen sesuai role!")
        role_select = st.selectbox("Role", options=list_role)
        file = st.file_uploader("Dokumen", type="pdf",accept_multiple_files=True)
        # """
        #     pilih role yang sesuai dengan name
        # """
        for i in role:
            if i['name'] == role_select:
                id_role_selected = i['id']
        # """
        #     upload file sesuai role yang dipilih
        # """        
        if st.button(f"upload {role_select}"):
            if file is not None:
               for i in file: 
                    result = upload_document(i, id_role_selected)
            else:
                st.toast("Please provide file!")    

def update_doc(file, id_role):
    if file is not None:
                today = datetime.today()
                formatted_time = today.strftime("%Y-%m-%d %H:%M:%S")
                update_document(file, id_role,formatted_time)
    else:
        st.toast("Please provide file!") 

# """
#     mendapatkan data count tipe feedback good/bad,
#     lalu tampilkan ke chart
# """
if data_count_feedback != "error":
    st.bar_chart(
            data_count_feedback,        
                 x="tipe", y="count")            

st.divider() 
st.header("Document Setting")    

# """
#     grouping data documents per role
#     e.g : {'manager':[..., ...], ...}
# """

group_doc = {}
for i in data_docs:
    name = i['name']
    if name not in group_doc:
        group_doc[name] = []
    group_doc[name].append(i)
            

file_upload_update = {}    
roles = ['--pilih--']
roles.extend([i for i in group_doc.keys()])
selected_role = None
selected_doc = None
selected_index = None
docs_id = None
with st.container(height=120):
    selected_role = st.selectbox("Role", options=roles)

with st.container(height=180):
    if selected_role is not '--pilih--':
        docs_title = [i['title'] for i in group_doc[selected_role]]
        docs_id = [i for i in group_doc[selected_role]]
        selected_doc = st.selectbox("Dokumen", options=docs_title, index=None, placeholder="search doc...")
        if selected_doc is not None:
            selected_index = docs_title.index(selected_doc)
        else:
            selected_role = None
    else:
        st.write("Dokumen")
        st.warning("Pilih role yang valid!")    
        selected_role = None


if selected_role is not None:
    # st.write(f"id : {docs_id[selected_index]['id']} | {selected_doc}")
    id_doc_update = docs_id[selected_index]['id']
    with st.container(height=180):
        file_update = st.file_uploader("upload update doc", type=["pdf"])
    col1, col2 = st.columns([0.2, 0.8], gap="small")
    with col1:
        if col1.button(f"✏ Update {selected_role}"):
            update_doc(file_update, id_doc_update)
    with col2:
        if col2.button(f"🗑 Delete {selected_role}", type="primary"):
            pass
            

st.divider()
st.title("Document Feedback")
feedback_doc = st.file_uploader(label="feedback doc", type="pdf")


    
        
st.sidebar.divider()            
if st.sidebar.button("Restart", use_container_width=True, type="primary"):
    pass              
            
    
################################
##       REBOOT               ##
################################       
# import os
# import subprocess
# import streamlit as st

# def reboot_streamlit():
#     # Gunakan subprocess untuk menjalankan ulang aplikasi Streamlit
#     python = os.path.basename(__file__)  # File Python yang sedang berjalan
#     command = f"streamlit run {python}"
#     subprocess.Popen(command, shell=True)
#     st.stop()  # Hentikan aplikasi saat ini agar restart

# if st.button("Restart App"):
#     reboot_streamlit()
    