import streamlit as st
from modelMsg.message_model import Message

USER = "user"
AI = "assistant"
MESSAGES = "messages"
msg: Message
@st.fragment
def read_conversation():
    """
        function untuk me-render ulang setiap percakapan
    """
    for idx, msg in enumerate(st.session_state[MESSAGES]):
        if msg.actor == AI:
            st.chat_message(AI, avatar="assets/fav.png").write(msg.payload)
        else:
            st.chat_message(USER, avatar="📌").write(msg.payload)
        if idx == (len(st.session_state[MESSAGES])-1) and 'final_doc' in st.session_state:
            with st.expander("Sumber Dokumen"):
                st.write(st.session_state.final_doc)    