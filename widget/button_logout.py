import streamlit as st
from layout.custom_layout import st_fixed_container
from streamlit_cookies_manager import EncryptedCookieManager
from controller.auth_controller import logout

USER = "user"
AI = "assistant"
MESSAGES = "messages"
def button_logout(cookies:EncryptedCookieManager):
    with st.sidebar:
        with st_fixed_container(mode="fixed", position="bottom", border=True, height=80, margin="bottom", key="asdasd"):
                if st.button("Log out 📤", use_container_width=True):
                    st.session_state[MESSAGES].clear()
                    del st.session_state.session_id
                    st.session_state.isSessionCreated = False
                    del st.session_state.isSessionCreated
                    del st.session_state.rag_init
                    ###########################
                    ##     hapus cookies     ##
                    ##########################
                    cookies['id'] = ""
                    cookies['username'] = ""
                    cookies['nik'] = "" 
                    cookies['role'] = "" 
                    cookies['name_role'] = ""
                    cookies['message'] = ""
                    cookies.save()
                    logout()
                    st.rerun()