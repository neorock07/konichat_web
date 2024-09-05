import streamlit as st
from controller.document_controller import upload_document
from controller.auth_controller import get_all_role

st.header("Admin Dashboard KoniChat")


role = get_all_role()
list_role = []
id_role_selected = None
for i in role:
    list_role.append(i['name'])
if role is not 'error' or role is not None:
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
        if file:
            result = upload_document(file, id_role_selected)

st.bar_chart([
    {"jual":20, "laba" : 100},
    {"jual":30, "laba" : 200},
    {"jual":15, "laba" : 80},
    ], x="jual", y="laba")            
        
    