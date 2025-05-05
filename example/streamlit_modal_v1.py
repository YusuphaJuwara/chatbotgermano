import streamlit as st
from streamlit_modal import Modal

import streamlit.components.v1 as components

if 'open_modal' not in st.session_state:
    st.session_state.open_modal = 0

st.markdown("Hi there")

# https://pypi.org/project/streamlit-modal/
modal = Modal(
    title="Demo Modal",
    key="demo-modal",
    
    # Optional
    padding=20,    # default value
    max_width=544  # default value
)
cols = st.columns(3)
for i in range(3):
    with cols[i]:
        if st.button(f"[{i}]", key=f"citation_{i}"):
            st.session_state.open_modal = i+1
            # modal.open()
            # display_citation_dialog(citation_id, docs_dict)
            
if st.session_state.open_modal != 0 and not modal.is_open():
    modal.open()
    
if st.session_state.open_modal != 0 and modal.is_open():
    with modal.container():
        chat_list_container = st.container(height=400, border=True)
        with chat_list_container:
            st.write("Text goes here")

            html_string = f'''
            <h1>HTML string in RED with ID: {st.session_state.open_modal}</h1>

            <script language="javascript">
            document.querySelector("h1").style.color = "red";
            </script>
            '''
            components.html(html_string)

            value = st.checkbox("Check me")
            st.write(f"Checkbox checked: {value}")
        
        # Button to close the modal AND reset the state variable
        if st.button("Close Citation", key=f"{st.session_state.open_modal}"):
            st.session_state.open_modal = 0
            modal.close()
            # *** Optimization Point ***
            # Rerun might be needed AFTER closing to ensure the main page
            # reflects any state changes made *while* the modal was open,
            # or just to ensure the trigger button logic resets correctly.
            # Test if it's necessary; sometimes modal.close() handles it.
            # st.rerun()