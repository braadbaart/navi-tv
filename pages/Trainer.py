import streamlit as st


st.write('AI trainer! Provide examples of what you want the AI to do.')
st.selectbox('Task', ['generate report', 'check status', 'send email', 'schedule meeting', 'create invoice'])

