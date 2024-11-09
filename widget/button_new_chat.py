import streamlit as st
import time
from streamlit_cookies_manager import EncryptedCookieManager

def button_new_chat(cookies:EncryptedCookieManager, MESSAGES:str):
    """
        function untuk membuat button new chat di sidebar, 
        kode ini juga akan membersihkan message yang terdahulu sebelum
        memulai chat yang baru, bergitu juga mengganti url params dengan 
        url `automodel`. 
        
        function ini juga akan refresh seluruh widget yang ada di window
        dengan menunggu selama 3 detik setelah widget ini di-tekan, untuk
        mengatasi bug url tidak terganti. 
    """
    
    if st.sidebar.button("New Chat 🌝"):
        st.toast("🚀Starting New Chat")
        st.query_params['c'] = "automodel"
        cookies["message"] = ""
        st.session_state[MESSAGES].clear()
        del st.session_state.session_id
        st.session_state.isSessionCreated = False
        del st.session_state.isSessionCreated
        time.sleep(3)
        st.rerun()