# in this file i have implemented the streaming functaionality in it 

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from langgraph_tool_backend import chatbot, retrieve_all_threads   # if you rename file with leading number

import uuid
# ***************************************************************utility functions**************
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_threads(st.session_state['thread_id'])
    st.session_state['message_history'] = [] 

def add_threads(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

# by this way we canextract all the  messages which are associated with the thread
def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    print(state.values)   
    return state.values.get('messages', [])  


# *****************************************************************session setup*********************
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_threads(st.session_state['thread_id'])

# *************************************************************store chat history in session************************
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

# *******************************************************************Side bar ui**********************
st.sidebar.title("LanfGraph Chatbot")

if st.sidebar.button("New chat"):
    reset_chat()

st.sidebar.header("My Conversations")


for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            else:
                role = "assistant"
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages
# ***************************************************************display previous messages******************
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])

# user input box
user_input = st.chat_input("type your message here")

if user_input:
    # add user message to history
    st.session_state["message_history"].append(
        {"role": "user", "content": user_input}
    )
    with st.chat_message("user"):
        st.text(user_input)

    # config , so  that we can see different threads chats in different sessions
    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {
            "thread_id": st.session_state["thread_id"]
        },
        "run_name": "chat_turn" # this represents the name for every message turn
    }
    # stream AI response, (generator part)
    with st.chat_message("assistant"):
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage): # it will display only if the message is from ai 
                    # yield only assistant tokens
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

