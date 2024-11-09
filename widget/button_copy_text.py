import streamlit as st
from controller.copytext import on_copy_click

@st.fragment     
def copy_button(ai_m):
    st.button("📄", on_click=on_copy_click, args=(ai_m )) 