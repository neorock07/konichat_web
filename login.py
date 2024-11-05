import streamlit as st
import logging
from controller.auth_controller import login
#############################
##      coba cookies       ##
#############################
from streamlit_cookies_manager import EncryptedCookieManager
import os
st.set_page_config("KoniChat | Login", page_icon="assets/fav.png")

cookies = EncryptedCookieManager(
    # This prefix will get added to all your cookie names.
    # This way you can run your app on Streamlit Cloud without cookie name clashes with other apps.
    prefix="konichat_chat",
    # You should really setup a long COOKIES_PASSWORD secret if you're running on Streamlit Cloud.
    password=os.environ.get("COOKIES_PASSWORD", "adhakshdkah3783432hjshfsdjfjsdfjsgfq393274sdjhfs"),
)

if not cookies.ready():
    # Wait for the component to load and send us current cookies.
    st.spinner("wait cookies...")
    st.stop()


# if "konichat_chat" in dict(cookies.keys()) :
# if cookies['id'] is not '':
if 'id' in cookies and cookies['id'] is not '': 
    st.switch_page("pages\\app.py")                    
    st.session_state.cookies_data = cookies

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
def handle_login(nik, password):
    if nik.isdigit() :
        text = login(int(nik), password)
        if text is not 'error':
            st.toast("✅ Login berhasil")
            st.session_state.logged_in = True
            st.session_state.user_data = text
            
            if text['name_role'] == 'admin':
                st.switch_page("pages\\bento.py")
            else:
                #untuk pengaturan cookies
                cookies['id'] = str(text['id']) 
                cookies['username'] = text['username']
                cookies['nik'] = str(text['nik']) 
                cookies['role'] = str(text['role']) 
                cookies['name_role'] = text['name_role']
                cookies.save()
                st.session_state.cookies_data = cookies
                
                st.switch_page("pages\\app.py")                    
        else:
            st.toast("❌ Login Gagal")
    else:
        st.warning("Mohon isi dengan format yang sesuai!")                    

col_title, col_img = st.columns(2)
col_title.title("Login Konichat")
col_title.subheader("Silahkan login untuk mengakses Konichat", divider="rainbow")
col_img.image(image="assets/fav.png")
            
with st.form('form'):
    nik = st.text_input(label="nik", type="default")
    password = st.text_input(label="password", type="password")
    sub_button = st.form_submit_button(label="Login")
    if sub_button:
        handle_login(nik, password)
           