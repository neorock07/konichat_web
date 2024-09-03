from modelMsg.prompt_model import Prompt
import time
import logging
import streamlit as st

logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)

# """
#     function untuk inference model, untuk melakukan conversation ke model.
#     params:
#         rag (Any) : isi dengan objek hasil assign ke RunnablePassThrough dan ke model LLM
#         input (Prompt) : field untuk menerima objek class Prompt sebagai pembungkus query ke model
#     returns:
#         respon (str) : hasil respon string model
#         response_time (float) : lama waktu respon model
# """

def inference(rag, input:Prompt):
    query = input.query
    role = input.role
    id = input.id
    
    if rag is not None:
            start_time = time.time()
            respon = ""
            # logger.debug(f"role : {role} | id_user {id} | cobo_chat_history_{id}")
            logger.debug(f"len : {len(st.session_state[f'chat_history_{st.session_state.session_id}'])} | chat_history_{st.session_state.session_id}")
            # logger.debug(f"len : {len(st.session_state[f'chat_history'])} | chat_history")

            if role == 1:
                respon = rag['rag_admin'].invoke(
                        {
                            "question": query,
                            # "chat_history": st.session_state[f"chat_history"]
                            "chat_history": st.session_state[f"chat_history_{st.session_state.session_id}"]
                        }
                    )
                
                if len(st.session_state[f"chat_history_{st.session_state.session_id}"]) >= 10:
                    st.session_state[f"chat_history_{st.session_state.session_id}"].pop(0)
                        
                # if len(st.session_state[f"chat_history"]) >= 10:
                #     st.session_state[f"chat_history"].pop(0)
                else:
                        
                    # st.session_state[f"chat_history"].extend(
                    st.session_state[f"chat_history_{st.session_state.session_id}"].extend(
                            [
                                f"human question : {query}",
                                f"your answer : {respon}" 
                            ]
                        )
                    # request.session[f"cobo_chat_history_{id}"] = chat_history
            else:
                respon = rag['rag_user'].invoke(
                        {
                            "question": query,
                            # "chat_history": st.session_state[f"chat_history"]
                            "chat_history": st.session_state[f"chat_history_{st.session_state.session_id}"]
                        }
                    )
                
                if len(st.session_state[f"chat_history_{st.session_state.session_id}"]) >= 10:
                    st.session_state[f"chat_history_{st.session_state.session_id}"].pop(0)
                        
                # if len(st.session_state[f"chat_history"]) >= 10:
                #     st.session_state[f"chat_history"].pop(0)
                else:
                    
                    # st.session_state[f"chat_history"].extend(
                    st.session_state[f"chat_history_{st.session_state.session_id}"].extend(
                            [
                                f"human question : {query}",
                                f"your answer : {respon}" 
                            ]
                        )
                # request.session[f"cobo_chat_history_{id}"] = chat_history   
            response_time = time.time() - start_time
            logger.debug(f"history : {st.session_state[f'chat_history_{st.session_state.session_id}']}")
    return respon.content, response_time