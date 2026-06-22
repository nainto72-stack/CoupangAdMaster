import streamlit as st
import time

def on_change():
    st.session_state.test_val = st.session_state.kw_mover_trigger
    print('Triggered:', st.session_state.kw_mover_trigger)

if 'test_val' not in st.session_state:
    st.session_state.test_val = ''

st.write('Current value:', st.session_state.test_val)
st.text_input('test', key='kw_mover_trigger', on_change=on_change)

import streamlit.components.v1 as components
components.html('''
    <script>
    setTimeout(function() {
        var input = window.parent.document.querySelector('input[aria-label="test"]');
        if (input) {
            var nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
            nativeSetter.call(input, "HELLO FROM JS");
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            // React 18 에서는 onBlur 혹은 Enter 이벤트로 강제 제출해야 on_change가 발동됨
            input.focus();
            setTimeout(function() {
                input.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
                input.blur();
            }, 50);
        }
    }, 2000);
    </script>
''', height=0, width=0)
