from streamlit_cookies_controller import CookieController
from streamlit import session_state as ss
import time
import streamlit as st
from controller.cookies_controller import cookies
import json

if "login_data" in cookies:
    user_data = json.loads(cookies["login_data"]) 
    st.info(user_data)


