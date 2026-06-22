import streamlit as st
st.text_input('test', max_chars=12345)
st.components.v1.html('<script>console.log(window.parent.document.body.innerHTML);</script>', height=0)
