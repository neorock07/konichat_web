import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import os
from dotenv import load_dotenv

load_dotenv()

def load_cookies():
    """
        kode ini digunakan untuk load cookies agar ketika
        browser di-refresh/close tetap akan dalam kondisi logged in
        dan supaya chat ketika di-refresh tidak hilang/terhapus.
    """
    
    SECRET_KEY = os.getenv('COOKIES_PASSWORD')  
    cookies = EncryptedCookieManager(
        prefix="konichat_chat",
        password=os.environ.get("COOKIES_PASSWORD",
                                #ini dapat diganti sesuai selera
                                SECRET_KEY),
    )

    if not cookies.ready():
        # Menunggu Cookies mendapatkan data
        st.spinner()
        st.stop()
        
    return cookies    
    
