import streamlit as st
import logging
from controller.auth_controller import login
# from controller.cookies_controller import cookies 
# import json

logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)


# """
#     function untuk handle hasil login
#     params:
#         nik : value nik
#         password: value password
#     returns:
#         None     
# """
st.set_page_config("KoniChat | Login", page_icon="assets/fav.png")
def handle_login(nik, password):
    if nik.isdigit() :
        text = login(int(nik), password)
        if text is not 'error':
            st.toast("✅ Login berhasil")
            st.session_state.logged_in = True
            st.session_state.user_data = text
            
             #simpan data login ke cookies
            # cookies["login_data"] = json.dumps(text)
            # cookies.save()
             
            # st.success("sukses saved successfully")
            if text['name_role'] == 'admin':
                st.switch_page("pages\\admin.py")
            else:
                # st.switch_page("pages\\bento.py")
                st.switch_page("pages\\app.py")
                    
        else:
            st.toast("❌ Login Gagal")
    else:
        st.warning("Mohon isi dengan format yang sesuai!")                    

# st.set_page_config(page_title="Konichat | login", page_icon="assets/fav.png")
col_title, col_img = st.columns(2)
col_title.title("Login Konichat")
col_title.subheader("Silahkan login untuk mengakses Konichat", divider="rainbow")
col_img.image(image="assets/fav.png")


# if "login_data" in cookies:
#     data_cookies = json.loads(cookies["login_data"]) 
#     # st.session_state.rag_init = True
#     st.session_state.user_data = data_cookies
#     if data_cookies['name_role'] == 'admin':
#         st.switch_page("pages\\admin.py")
#     else:
#         st.switch_page("pages\\app.py")
    
        
# else:    
with st.form('form'):
    nik = st.text_input(label="nik", type="default")
    password = st.text_input(label="password", type="password")
    sub_button = st.form_submit_button(label="Login")
    if sub_button:
        handle_login(nik, password)
           