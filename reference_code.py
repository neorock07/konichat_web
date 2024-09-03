from langchain.chat_models import AzureChatOpenAI
from langchain.memory import ConversationBufferWindowMemory # ConversationBufferMemory
from langchain.agents import ConversationalChatAgent, AgentExecutor, AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import pprint
import streamlit as st
import os
import pandas as pd
from streamlit_feedback import streamlit_feedback

def handle_feedback():  
    st.write(st.session_state.fb_k)
    st.toast("✔️ Feedback received!")

  
os.environ["OPENAI_API_KEY"] = ...
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_BASE"] = ...
os.environ["OPENAI_API_VERSION"] = "2023-08-01-preview"


@st.cache_data(ttl=72000)
def load_data_(path):
    return pd.read_csv(path) 

uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    # If a file is uploaded, load the uploaded file
    st.session_state["df"] = load_data_(uploaded_file)


if "df" in st.session_state:

    msgs = StreamlitChatMessageHistory()
    memory = ConversationBufferWindowMemory(chat_memory=msgs, 
                                            return_messages=True, 
                                            k=5, 
                                            memory_key="chat_history", 
                                            output_key="output")
    if len(msgs.messages) == 0 or st.sidebar.button("Reset chat history"):
        msgs.clear()
        msgs.add_ai_message("How can I help you?")
        st.session_state.steps = {}
    avatars = {"human": "user", "ai": "assistant"}
    for idx, msg in enumerate(msgs.messages):
        with st.chat_message(avatars[msg.type]):
            # Render intermediate steps if any were saved
            for step in st.session_state.steps.get(str(idx), []):
                if step[0].tool == "_Exception":
                    continue
                # Insert a status container to display output from long-running tasks.
                with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                    st.write(step[0].log)
                    st.write(step[1])
            st.write(msg.content)


    if prompt := st.chat_input(placeholder=""):
        st.chat_message("user").write(prompt)

        llm = AzureChatOpenAI(
                        deployment_name = "gpt-4",
                        model_name = "gpt-4",
                        openai_api_key = os.environ["OPENAI_API_KEY"],
                        openai_api_version = os.environ["OPENAI_API_VERSION"],
                        openai_api_base = os.environ["OPENAI_API_BASE"],
                        temperature = 0, 
                        streaming=True
                        )

        prompt_ = PromptTemplate(
            input_variables=["query"],
            template="{query}"
        )
        chain_llm = LLMChain(llm=llm, prompt=prompt_)
        tool_llm_node = Tool(
            name='Large Language Model Node',
            func=chain_llm.run,
            description='This tool is useful when you need to answer general purpose queries with a large language model.'
        )

        tools = [tool_llm_node] 
        chat_agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools)

        executor = AgentExecutor.from_agent_and_tools(
                                                        agent=chat_agent,
                                                        tools=tools,
                                                        memory=memory,
                                                        return_intermediate_steps=True,
                                                        handle_parsing_errors=True,
                                                        verbose=True,
                                                    )
        

        with st.chat_message("assistant"):            
            
            st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
            response = executor(prompt, callbacks=[st_cb, st.session_state['handler']])
            st.write(response["output"])
            st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]
            response_str = f'{response}'
            pp = pprint.PrettyPrinter(indent=4)
            pretty_response = pp.pformat(response_str)
              

        with st.form('form'):
            streamlit_feedback(feedback_type="thumbs",
                                optional_text_label="[Optional] Please provide an explanation", 
                                align="flex-start", 
                                key='fb_k')
            st.form_submit_button('Save feedback', on_click=handle_feedback)