import streamlit as st

st.text_input('Hidden Input', key='my_input', label_visibility='collapsed')

js = """
<script>
setTimeout(function(){
    try {
        var parentDoc = window.parent.document;
        var input = parentDoc.querySelector('input[aria-label="Hidden Input"]');
        if(input) {
            console.log("Found via aria-label!");
            input.parentElement.parentElement.style.display = 'none'; // hide it just to test
        } else {
            console.log("Not found via aria-label");
        }
    } catch (e) {
        console.error(e);
    }
}, 1000);
</script>
"""
import streamlit.components.v1 as components
components.html(js, height=0)
