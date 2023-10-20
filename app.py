"""
This is a Streamlit app that uses a custom component called streamlit_chat to create a chatbot interface. 
The chatbot uses the OpenAI API to generate responses to user input. 
The app also includes a sidebar that displays the output of certain chatbot functions.

> streamlit != streamlit_chat. streamlit_chat is a custom component.

streamlit_chat uses the avarta_style from https://www.dicebear.com/styles/.

https://docs.streamlit.io/library/cheatsheet
"""
import time
import streamlit as st
import logging
from uuid import uuid4 as uuid
from streamlit_chat import message
from module.chat_flow import ChatBot
from module.method_util import get_func_list

# Logging configuration
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("output.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def on_clear_msgs():
    st.session_state.messages = []
    st.session_state.odsl = []


header_img = st.empty()
header_img.image(
    "https://dwglogo.com/wp-content/uploads/2019/03/1600px-OpenAI_logo-1024x705.png",
    width=80,
)

st.title("Mini-Copilot")
st.button("Clear message", on_click=on_clear_msgs)

if "messages" not in st.session_state:
    st.session_state.chat = ChatBot()
    st.session_state["messages"] = []
    st.session_state["odsl"] = []

chat_container = st.container()
sidebar_container = st.sidebar
# sidebar width
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"]{
        min-width: 40%;
        max-width: 40%;
    }
    """,
    unsafe_allow_html=True,
)


with chat_container:
    for _message in st.session_state.messages:
        if _message["role"] == "user":
            message(key=str(uuid()), message=_message["content"], is_user=True,
                    avatar_style="lorelei-neutral")
        else:
            message(key=str(uuid()),
                    message=_message["content"], avatar_style="micah")

    prompt = chat_container.chat_input("Ask me...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        message(key=str(uuid()), message=prompt,
                is_user=True, avatar_style="lorelei-neutral")

        respond = ''
        with st.chat_message("assistant"):
            try:
                respond = st.session_state.chat.send_message(prompt)
            except Exception as e:
                st.error(e)

        messages = []
        time.sleep(0.5)

        if respond:
            message(respond, avatar_style="micah")
            st.session_state.messages.append(
                {"role": "assistant", "content": respond})

            func_list = get_func_list()

            if any(func in respond for func in func_list):
                st.session_state.odsl.append(respond)


with sidebar_container:
    sidebar_inner_container = st.container()
    sidebar_inner_container.write("ODSL output:")
    sidebar_inner_container.markdown(
        '```print("Hello world! output goes here")```')

    for _message in st.session_state.odsl:
        sidebar_inner_container.markdown(f'```{_message}```')
