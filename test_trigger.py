import streamlit as st

if 'test_val' not in st.session_state:
    st.session_state.test_val = ''

st.write('Current value:', st.session_state.test_val)

def on_change():
    st.session_state.test_val = st.session_state.my_input
    print("Triggered from JS! New value:", st.session_state.test_val)

st.text_input('Hidden Input', key='my_input', on_change=on_change)

js = """
<script>
setTimeout(function(){
    try {
        var parentDoc = window.parent.document;
        var label = parentDoc.evaluate("//p[text()='Hidden Input']", parentDoc, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
        if(label) {
            var input = label.closest('div[data-testid="stTextInput"]').querySelector('input');
            var nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
            nativeSetter.call(input, 'Triggered ' + Date.now());
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
            input.focus();
            setTimeout(function(){ input.blur(); }, 100);
            console.log("JS Triggered the input!");
        } else {
            console.log("Could not find label");
        }
    } catch (e) {
        console.error(e);
    }
}, 3000);
</script>
"""
import streamlit.components.v1 as components
components.html(js, height=0)
