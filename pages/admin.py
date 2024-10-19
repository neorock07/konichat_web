from httpx import delete
import streamlit as st
from controller.document_controller import delete_docs, upload_document
from controller.document_controller import update_document
from controller.auth_controller import get_all_role
from controller.feedback_method import get_count_feedback, get_bad_feedback
from controller.document_controller import get_all_docs, get_feedback_doc, upload_document_feedback, get_feedback_doc_by_id
from controller.document_controller import delete_docs,delete_feedback_docs
from datetime import datetime
import docx
from io import BytesIO
import os
import subprocess
import streamlit as st
import pyautogui
import time

st.set_page_config("KoniChat | Admin", page_icon="assets/fav.png")

st.header("Chatbot Performance")

role = get_all_role()
data_count_feedback = get_count_feedback()
data_docs = get_all_docs()
list_role = []
roles_feed = []
id_role_selected = None
for i in role:
    list_role.append(i['name'])
    roles_feed.append({i['name'] : i['id']})    
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
            st.rerun()    

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
    

          

########################################################################
##                     Dokumen Sumber                                 ##
########################################################################
@st.fragment
@st.dialog(title= "Yakin ingin menghapus?")
def dialog_konf_doc(id_doc):
    if st.button("Yakin"):
        delete_docs(id_doc)
        st.rerun()

roles = None
@st.fragment
def widget_doc_sumber():    
    st.divider() 
    st.header("Update Document Sumber")    
    global roles
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
        id_doc_update = docs_id[selected_index]['id']
        with st.container(height=180):
            file_update = st.file_uploader("upload update doc", type=["pdf"])
        col1, col2 = st.columns([0.2, 0.8], gap="small")
        with col1:
            if col1.button(f"✏ Update {selected_role}"):
                update_doc(file_update, id_doc_update)
        with col2:
            if col2.button(f"🗑 Delete {selected_role}", type="primary"):
                # delete_docs(id_doc_update)
                dialog_konf_doc(id_doc_update)
            
widget_doc_sumber()
########################################################################
##                     Dokumen Feedback                               ##
########################################################################

@st.fragment
@st.dialog(title= "Yakin ingin menghapus?")
def dialog_konf_feedback(id_role):
    if st.button("Yakin"):
        delete_feedback_docs(id_role)
        st.rerun()


@st.fragment
def widgt_doc_feedback(roles):
    st.divider()
    st.title("Document Feedback")

    with st.container(height=120):
        opt = []
        for key, val in enumerate(roles):
            opt.append(next(iter(val))) 
        selected_role_feed = st.selectbox("Role", options=opt, key="asdasudhau")

    
    id_role_to_feed = None
    if selected_role_feed is not '--pilih--':
            for i in roles:
                if selected_role_feed == next(iter(i)):
                    id_role_to_feed = i[selected_role_feed]
            doc_feeds = get_feedback_doc_by_id(id_role_to_feed)
            
            if doc_feeds is not None:
                st.caption(f"Nama file : {doc_feeds['title']}") 
            else:
                st.warning("⚠ Data Masih Kosong! Silahkan Tambahkan")
            
            docs = docx.Document()
            bad_data = get_bad_feedback(id_role=id_role_to_feed)
            if isinstance(bad_data, str):
                    pass
            else:
                    for i in range(len(bad_data)):
                            docs.add_paragraph("").add_run(f"{i+1}. Query : ").bold = True
                            docs.add_paragraph(bad_data[i]['human_query'])
                            docs.add_paragraph("").add_run(f"Your Rejected Response : ").bold = True
                            docs.add_paragraph(bad_data[i]['ai_respon'])
                            docs.add_paragraph("").add_run(f"Your Chosen Response : ").bold = True
                            docs.add_paragraph("<EOS>")
                            
                    # Simpan dokumen ke dalam memori
                    buffer = BytesIO()
                    docs.save(buffer)
                    buffer.seek(0)
                        
                    st.download_button(
                                label="Unduh feedback user",
                                data=buffer,
                                file_name=f"dokumen_revisi_{selected_role_feed}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
            
            feedback_doc = st.file_uploader(label="Upload feedback document", type="pdf")
            
            kol1, kol2 = st.columns([0.2, 0.8], gap="small")
            with kol1:
                if kol1.button(f"✏ Upload {selected_role_feed}"):
                            if feedback_doc is not None:
                                upload_document_feedback(feedback_doc, id_role_to_feed)

                            else:
                                    st.toast("❗ Please select a Document")    
            with kol2:
                if kol2.button(f"🗑 Delete {selected_role_feed}", type="primary"):
                        # st.warning("Yakin ingin menghapus ?")
                        # delete_feedback_docs(id_role_to_feed)
                        dialog_konf_feedback(id_role_to_feed)
                                      
    else:
            st.warning("Pilih role yang valid!")    
            selected_role_feed = None

widgt_doc_feedback(roles_feed)
    
        
            
    
################################
##       REBOOT               ##
################################       


# def reboot_streamlit():
#     # Gunakan subprocess untuk menjalankan ulang aplikasi Streamlit
#     current_file_path = os.path.abspath(__file__)

#     # Mendapatkan path ke direktori root_project (satu folder ke atas dari folder 'controller')
#     root_project_path = os.path.dirname(os.path.dirname(current_file_path))

#     # Mendapatkan path absolut ke login.py
#     login_path = os.path.join(root_project_path, 'login.py') # File Python yang sedang berjalan
#     command = f"streamlit run {login_path}"
#     subprocess.Popen(command, shell=True)
#     st.stop()

def reboot_streamlit():
    # Tentukan port yang digunakan Streamlit (8501)
    port = 8501

    # Dapatkan path ke file yang ingin dijalankan ulang
    current_file_path = os.path.abspath(__file__)
    root_project_path = os.path.dirname(os.path.dirname(current_file_path))
    login_path = os.path.join(root_project_path, 'login.py')
     # Memberikan waktu sejenak sebelum melakukan penekanan Ctrl+C
    time.sleep(1)  # Memberi jeda sebelum simulasi Ctrl+C
    
    # Simulasi Ctrl+C untuk menghentikan server Streamlit
    pyautogui.hotkey('ctrl', 'c')

    # Memberikan waktu agar server dapat berhenti sepenuhnya
    time.sleep(60)    
    # Jalankan kembali Streamlit di port yang sama
    command = f"streamlit run {login_path} --server.port {port}"
    subprocess.Popen(command, shell=True)

    # Hentikan eksekusi Streamlit saat ini
    st.stop()
# if st.button("Restart App"):
#     reboot_streamlit()

st.sidebar.divider()            
if st.sidebar.button("Restart", use_container_width=True, type="primary"):
    reboot_streamlit()