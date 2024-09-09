from turtle import onclick
import streamlit as st
from controller.document_controller import upload_document
from controller.document_controller import update_document
from controller.auth_controller import get_all_role
from controller.feedback_method import get_count_feedback
from controller.document_controller import get_all_docs
from datetime import datetime
import uuid
from annotated_text import annotated_text

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
        st.warning("Upload dokumen sesuai role!")
        role_select = st.selectbox("Role", options=list_role)
        file = st.file_uploader("Dokumen", type="pdf",accept_multiple_files=False)
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
                result = upload_document(file, id_role_selected)
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

st.header("Document per Role")    
for i in data_docs:
    with st.container(height=320):
        col1, col2 = st.columns(2, gap="small")
        with col1:
            # st.write(f"{i['name']}" )
            annotated_text(
                (f"{i['name']}","role", "#773034"),
            )
        with col2:
            datetime_obj = datetime.strptime(i['tanggal'], "%Y-%m-%dT%H:%M:%S.%fZ")
            # Mengubah ke format tanggal biasa
            formatted_date = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
            col2.write(f"🕖 terakhir update : {formatted_date}")
        st.write(f"Dok. sekarang : {i['title']}" )
        file = st.file_uploader("Dokumen", type="pdf",accept_multiple_files=False,key=i['id'])

        # """
        #     upload file sesuai role yang dipilih
        # """
        dt = [file, i['id_role']]        
        st.button(f"update {i['name']}",
                  key=uuid.uuid4().hex,
                  on_click=lambda dta = [file, i['id_role']] : update_doc(dta[0], dta[1]))

st.sidebar.divider()            
if st.sidebar.button("Restart", use_container_width=True, type="primary"):
    pass              
            
    
       
    