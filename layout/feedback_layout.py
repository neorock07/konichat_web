import logging
import streamlit as st

 
def save_feedback(msg, topik):
    st.toast(f"hallo coeg!! | {msg} | {topik}")

def feedback_form():
    global selected
    map_data = ["good", "bad"]
    selected = st.feedback("thumbs")  # Misal mengganti st.feedback dengan st.radio
    if selected is not None:
        save_feedback(map_data[selected], "gethuk")
        logging.debug(map_data[selected])
        st.toast("feedback ono!")
    else:
        st.toast("feedback ra ono!")        
    # with st.form('form_feedback'):
    #     st.caption("Optional feedback")
        
    #     # Ambil input dari pengguna
    #     topik = st.text_input("Topik feedback")
        
    #     # Tombol submit
    #     submit = st.form_submit_button("Submit")
        
    #     # Cek apakah tombol submit ditekan
    # if submit:
    #         # Setelah submit, panggil fungsi untuk menyimpan feedback
    #     save_feedback(selected, topik)