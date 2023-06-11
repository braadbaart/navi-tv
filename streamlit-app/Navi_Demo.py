import base64
import redis
import streamlit as st

st.set_page_config(
    page_title='Navi demo',
    page_icon='images/logo.png',
    layout='wide',
)

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <conversational_style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </conversational_style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)


# def check_password():
#     def password_entered():
#         if (
#             st.session_state["username"] in st.secrets["passwords"]
#             and st.session_state["password"]
#             == st.secrets["passwords"][st.session_state["username"]]
#         ):
#             st.session_state["password_correct"] = True
#             del st.session_state["password"]
#             del st.session_state["username"]
#         else:
#             st.session_state["password_correct"] = False
#
#     if "password_correct" not in st.session_state:
#         st.text_input("Username", on_change=password_entered, key="username")
#         st.text_input(
#             "Password", type="password", on_change=password_entered, key="password"
#         )
#         return False
#     elif not st.session_state["password_correct"]:
#         st.text_input("Username", on_change=password_entered, key="username")
#         st.text_input(
#             "Password", type="password", on_change=password_entered, key="password"
#         )
#         st.error("😕 User not known or password incorrect")
#         return False
#     else:
#         return True


# set_background("images/earth_globe.png")
#
#
# if check_password():
set_background("images/night_sky.png")


@st.cache_resource
def init_connection():
    return redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


conn = init_connection()
conversational_style = st.selectbox(
    'Select a conversational conversational_style',
    ['quirky', 'dead serious', 'millennial', 'boomer', 'drunk', 'gen_x']
)

st.session_state['conversational_style'] = conversational_style

user_interests = st.multiselect(
    'Select your favorite activities', ['surfing', 'climbing', 'chess', 'reading', 'drinking']
)
st.session_state['interests'] = user_interests

st.write(f'You have selected the following conversational conversational_style: {conversational_style}')
st.write(f'We\'ve registered the following interests: {", ".join(user_interests)}.')
