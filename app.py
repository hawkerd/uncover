import streamlit as st
from client import MCPOpenAIClient
import dotenv
import logging
import asyncio
import nest_asyncio

nest_asyncio.apply()


# configure logging
logging.basicConfig(level=logging.INFO)

# load environment variables from .env file
dotenv.load_dotenv()

st.title("Uncover")

# set up session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "client" not in st.session_state:
    st.session_state.client = MCPOpenAIClient()
    st.session_state.client.connect_to_server("http://localhost:8050/mcp")


for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Say something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response = st.session_state.client.process_query(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
