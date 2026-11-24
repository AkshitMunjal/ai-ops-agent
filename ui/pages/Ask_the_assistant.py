import httpx
import streamlit as st

from ui.agent_api_client import ask_assistant

st.set_page_config(page_title="Ask the assistant", layout="centered")
st.title("Ask the assistant")
st.caption(
    "It answers from live ERP data and from the written company policies. "
    "It can only read. It cannot create, approve or send anything."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.sidebar.button("Clear chat"):
    st.session_state.messages = []
    st.rerun()


def show_message(message):
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message.get("tools_used"):
            st.caption("Looked at: " + ", ".join(message["tools_used"]))

        if message.get("sources"):
            st.caption("Documents found: " + ", ".join(message["sources"]))


for old_message in st.session_state.messages:
    show_message(old_message)

question = st.chat_input("Ask about stock, orders, invoices or policies")

if question:
    history = []
    for old_message in st.session_state.messages:
        history.append({"role": old_message["role"], "content": old_message["content"]})

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Looking it up..."):
            try:
                result = ask_assistant(question, history)
            except httpx.HTTPError:
                result = None

        if result is None:
            st.error("The assistant could not be reached. Is the agent service running on port 8001?")
        else:
            st.write(result["answer"])

            if result["tools_used"]:
                st.caption("Looked at: " + ", ".join(result["tools_used"]))

            if result["sources"]:
                st.caption("Documents found: " + ", ".join(result["sources"]))

    if result is not None:
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "tools_used": result["tools_used"],
                "sources": result["sources"],
            }
        )
