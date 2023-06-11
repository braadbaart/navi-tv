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
from langchain.memory import ConversationBufferMemory
from langchain.memory import ChatMessageHistory

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

llm = ChatOpenAI(openai_api_key=st.secrets['llms']['openai_api_key'], temperature=0)
memory = ConversationBufferMemory(return_messages=True)
conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm)


if 'conversation_history' not in st.session_state:
    st.session_state['agent'] = [f"Welcome to {conversational_style} Navi, how may I help you?"]
    st.session_state['human'] = ['']
# else:


# Layout of input/response containers
input_container = st.container()
colored_header(label='', description='', color_name='orange-70')
response_container = st.container()
history = ChatMessageHistory()


def get_text():
    input_text = st.text_input("You: ", "", key="input")
    memory.chat_memory.add_user_message(input_text)
    history.add_user_message(input_text)
    return input_text


with input_container:
    user_input = get_text()
    st.session_state["text"] = ""


def generate_response(user_prompt):
    agent_response = conversation.predict(input=user_prompt)
    memory.chat_memory.add_ai_message(agent_response)
    history.add_ai_message(agent_response)
    return agent_response


with response_container:
    if user_input:
        response = generate_response(user_input)
        st.session_state.human.append(user_input)
        st.session_state.agent.append(response)

    if st.session_state['agent']:
        for i in range(len(st.session_state['agent'])):
            message(st.session_state['human'][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["agent"][i], key=str(i))
