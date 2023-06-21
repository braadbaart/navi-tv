import os
import redis
import streamlit as st

from streamlit_chat import message
from streamlit_extras.colored_header import colored_header

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory, RedisChatMessageHistory
from langchain.schema import messages_to_dict

st.set_page_config(page_title='Navi conversational AI agent demo')
st.session_state.waiting_for_user_input = True
st.write(st.session_state)
username = 'grumpy_old_fool'

file_path = os.path.dirname(__file__)
conversational_style = st.session_state['conversational_style'] if 'conversational_style' in st.session_state else ''
interests = ', '.join(st.session_state['interests']) if 'interests' in st.session_state else ''


@st.cache_resource
def init_userdb_connection():
    return redis.StrictRedis(host='localhost', port=st.secrets['redis']['port'], db=0)


userdb = init_userdb_connection()


@st.cache_resource
def init_conversationdb_connection():
    return redis.StrictRedis(host='localhost', port=st.secrets['redis']['port'], db=1)


convdb = init_conversationdb_connection()


prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template_file(
        template_file=os.path.join(file_path, '../prompts/agent/style.yaml'),
        input_variables=['conversational_style', 'agent_interests']
    ).format(
        conversational_style=conversational_style,
        agent_interests=interests
    ),
    MessagesPlaceholder(variable_name='history'),
    HumanMessagePromptTemplate.from_template('{input}')
])


@st.cache_resource
def get_memory():
    user_conversation_memory = ConversationBufferWindowMemory(return_messages=True, k=10)
    return user_conversation_memory


@st.cache_resource
def load_emotion_recognition_model():
    tokenizer = AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-emotion")
    model = AutoModelForSeq2SeqLM.from_pretrained("mrm8488/t5-base-finetuned-emotion")
    return tokenizer, model


er_tokenizer, er_model = load_emotion_recognition_model()


def detect_emotion(text):
    input_ids = er_tokenizer.encode(text + '</s>', return_tensors='pt')
    output = er_model.generate(input_ids=input_ids, max_length=2)
    dec = [er_tokenizer.decode(ids) for ids in output]
    label = dec[0]
    return label.replace('<pad> ', '').replace(' <pad>', '')


def get_history():
    return RedisChatMessageHistory(session_id=username, url='redis://localhost:6379/1', key_prefix=':conv')


llm = ChatOpenAI(openai_api_key=st.secrets['llms']['openai_api_key'], temperature=0.8)
memory = get_memory()
history = get_history()
conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm)

# Layout of input/response containers
colored_header(label='', description='', color_name='orange-70')
dialogue_container = st.container()
input_container = st.container()


if len(messages_to_dict(history.messages)) == 0:
    agent_message = f'Welcome to {conversational_style} Navi, how may I help you?'
    memory.chat_memory.add_ai_message(agent_message)
    history.add_ai_message(agent_message)
    st.session_state.waiting_for_user_input = True


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
    st.text_input('You: ', value='', key='chat_dialogue_box', on_change=process_user_input)
    if st.session_state.user_message:
        memory.chat_memory.add_user_message(st.session_state.user_message)
        history.add_user_message(st.session_state.user_message)
        generate_response(st.session_state.user_message)
        st.session_state.chat_log = messages_to_dict(history.messages)
        st.session_state.user_emotion = detect_emotion(st.session_state.user_message)


with dialogue_container:
    chat_history = messages_to_dict(history.messages)
    if st.session_state.waiting_for_user_input:
        for i in range(len(chat_history)):
            if chat_history[i]['type'] == 'ai':
                message(chat_history[i]['data']['content'], avatar_style='bottts', seed=3, key=str(i))
            else:
                message(
                    chat_history[i]['data']['content'], avatar_style='personas', seed=4,
                    is_user=True, key=str(i) + '_user'
                )
