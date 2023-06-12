import os
import redis
import streamlit as st

from streamlit_chat import message
from streamlit_extras.colored_header import colored_header

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory import ChatMessageHistory
from langchain.schema import messages_from_dict, messages_to_dict

st.set_page_config(page_title="Navi conversational AI agent demo")
st.write(st.session_state)

file_path = os.path.dirname(__file__)
conversational_style = st.session_state['conversational_style'] if 'conversational_style' in st.session_state else 'gen X'
interests = ', '.join(st.session_state['interests']) if 'interests' in st.session_state else 'chatbots'


@st.cache_data(ttl=600)
def get_user_conversation_history(user_id):
    return True


prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template_file(
        template_file=os.path.join(file_path, '../prompts/agent/style.yaml'),
        input_variables=["conversational_style", "agent_interests"]
    ).format(
        conversational_style=conversational_style,
        agent_interests=interests
    ),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{input}")
])


@st.cache_resource
def get_memory():
    user_conversation_memory = ConversationBufferWindowMemory(return_messages=True, k=10)
    return user_conversation_memory


@st.cache_resource
def get_history():
    user_conversation_history = ChatMessageHistory()
    return user_conversation_history


llm = ChatOpenAI(openai_api_key=st.secrets['llms']['openai_api_key'], temperature=0.8)
memory = get_memory()
history = get_history()
conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm)

# Layout of input/response containers
colored_header(label='', description='', color_name='orange-70')
dialogue_container = st.container()
input_container = st.container()


if len(messages_to_dict(history.messages)) == 0:
    agent_message = f"Welcome to {conversational_style} Navi, how may I help you?"
    memory.chat_memory.add_ai_message(agent_message)
    history.add_ai_message(agent_message)
    st.session_state.waiting_for_user_input = True
# else:


if 'user_message' not in st.session_state:
    st.session_state.user_message = ''


def process_user_input():
    st.session_state.user_message = st.session_state.chat_dialogue_box
    st.session_state.chat_dialogue_box = ''


def generate_response(user_prompt):
    agent_response = conversation.predict(input=user_prompt)
    memory.chat_memory.add_ai_message(agent_response)
    history.add_ai_message(agent_response)


with input_container:
    st.text_input("You: ", value="", key="chat_dialogue_box", on_change=process_user_input)
    if st.session_state.user_message:
        memory.chat_memory.add_user_message(st.session_state.user_message)
        history.add_user_message(st.session_state.user_message)
        generate_response(st.session_state.user_message)
        st.session_state.chat_log = messages_to_dict(history.messages)


with dialogue_container:
    chat_history = messages_to_dict(history.messages)
    if st.session_state.waiting_for_user_input:
        for i in range(len(chat_history)):
            if chat_history[i]['type'] == 'ai':
                message(chat_history[i]['data']['content'], key=str(i))
            else:
                message(chat_history[i]['data']['content'], is_user=True, key=str(i) + '_user')
