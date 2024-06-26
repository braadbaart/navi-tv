import redis
import base64
import streamlit as st

st.set_page_config(
    page_title='Navi TV',
    page_icon='images/logo.png',
    layout='wide',
)

username = 'ok_boomer'

st.markdown('**Welcome to Navi TV!** 📺')
st.markdown('Your own home-grown personal multimedia brewery - where the Hallmark channel meets MTV inside an LLM 📺♥️🤖')


def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)


set_background("images/night_sky.png")


@st.cache_resource
def init_userdb_connection():
    return redis.StrictRedis(
        host=st.secrets['redis']['host'],
        port=st.secrets['redis']['port'],
        charset="utf-8",
        decode_responses=True,
        db=0
    )


userdb = init_userdb_connection()


def get_user_data():
    userdata = userdb.hgetall(username)
    if userdata:
        return userdata
    else:
        userdb.hset(username, 'user_data', username)
        return {'user_data': username}


user_data = get_user_data()
st.write(user_data)
style_options = ['quirky', 'dead serious', 'millennial', 'boomer', 'drunk', 'gen_x']
conversational_style = st.selectbox(
    'Preferred conversational style',
    style_options,
    index=style_options.index(user_data.get('conversational_style', 'quirky'))
)
if conversational_style != user_data.get('conversational_style'):
    st.write(f'Saving new conversational style: {conversational_style}')
    userdb.hset(username, 'conversational_style', conversational_style)

st.session_state['conversational_style'] = conversational_style

saved_user_interests = user_data.get('user_interests').split(',') if user_data.get('user_interests', None) else None


def update_user_interests():
    if user_interests and set(user_interests) != set(user_data.get('user_interests', '').split(',')):
        userdb.hset(username, 'user_interests', ','.join(user_interests))


user_interests = st.multiselect(
    'Select your favorite activities', ['surfing', 'climbing', 'chess', 'reading', 'drinking'],
    default=saved_user_interests, on_change=update_user_interests
)

st.session_state['interests'] = user_interests

st.write(f'You have selected the following conversational conversational_style: {conversational_style}')
st.write(f'We\'ve registered the following interests: {", ".join(user_interests)}.')
st.write('We\'ll use this information to personalize your experience.')

