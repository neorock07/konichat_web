import streamlit as st
from modelMsg.message_model import Message

USER = "user"
AI = "assistant"
MESSAGES = "messages"
def widget_chat():
    """
        function untuk membuat widget chatbox
        - **params**:
            -
        - **returns**:
            prompt (str) : prompt user yang diketik di widget ini.     
    """
    
    if st.session_state.rag_chain is not None:
        prompt: str = st.chat_input("chat disini!")
    else:
        prompt: str = st.chat_input("chat disini!", disabled=True)
    
    return prompt    

@st.fragment
def assignMessage(prompt):
    """
        Function untuk menambahkan prompt yang dikirim user 
        lewat widget chatbox ke session untuk digunakan pada proses
        inference ke LLM dan digunakan pada list `chat_history`.
        dan juga menampilkan prompt tersebut di widget `st.chat_message`
    """
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    st.chat_message(USER, avatar="📌").write(prompt)