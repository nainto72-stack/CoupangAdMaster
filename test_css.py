import streamlit as st

st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Hidden Input']) { display: none !important; }</style>", unsafe_allow_html=True)

st.text_input('Hidden Input', key='my_input', label_visibility='collapsed')
st.write("If you only see this text and no input boxes, it worked!")
