import streamlit as st
from controller.feedback_method import feedback
from streamlit_feedback import streamlit_feedback
from functools import partial

def handle_feedback(ai_respon, human_query, role):
        """
            data ini digunakan sebagai callback function widget feedback, 
            untuk mengirim data feedback ke server.
        """
        
        if st.session_state.fb_k is not None:  
            ulasan = dict(st.session_state.fb_k)
            feedback(ulasan['score'], ulasan['text'], ai_respon, human_query, role)
        else:
            st.toast("Sorry, your feedback could not be saved!")     

def widget_feedback(ai_respon, human_query, role):
    """
    function ini digunakan untuk membuat widget feedback.
    """
    with st.form('form'):
        
        feedbck = streamlit_feedback(feedback_type="thumbs",
                                     optional_text_label="Berikan ulasanmu!", 
                                     align="flex-start", 
                                     key='fb_k')
        st.form_submit_button('Save feedback', 
                              on_click=partial(handle_feedback, ai_respon, human_query, role))

