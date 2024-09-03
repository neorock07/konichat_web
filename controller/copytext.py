import streamlit as st
import clipboard

# """
# function untuk copy message, diterapkan setelah muncul di chat.
#     params:
#         text (str) : message
#     return:
#         None    
# """

def on_copy_click(text):
    st.session_state.copied = text
    clipboard.copy(text)
