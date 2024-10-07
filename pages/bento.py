# from openai import OpenAI

# client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# client.chat.completions.create(
#             model=st.session_state["openai_model"],
#             messages=[
#                 {"role": m["role"], "content": m["content"]}
#                 for m in st.session_state.messages
#             ],
#             stream=True,
#         )