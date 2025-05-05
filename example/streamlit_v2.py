import datetime
import random, time
import re
import uuid
from html import escape
import streamlit as st
import streamlit.components.v1 as components
from streamlit_modal import Modal

# --- Configuration & Session State Initialization ---
def initialize_app():
    """Initialize app configuration and session state variables."""
    # Modal configuration
    modal = Modal(
        title="Demo Modal",
        key="demo-modal",
        padding=20,
    )
    
    # Page configuration
    st.set_page_config(layout="centered",
                    page_title="Chat App",
                    page_icon="🤖",
                    menu_items={
                                'Get Help': 'https://www.extremelycoolapp.com/help', 
                                'Report a bug': "https://www.extremelycoolapp.com/bug", 
                                'About': "# This is a header. This is an *extremely* cool app!"
                        },
                    )

    # Initialize session state variables if they don't exist
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {"name": "User", "avatar": "👤"}
    if "chat_sessions" not in st.session_state:
        # Structure: {session_id: {"title": "...", "messages": [{"role": "user/assistant", "content": "...", "link": "optional_url"}]}}
        st.session_state.chat_sessions = {}
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "open_modal" not in st.session_state:
        st.session_state.open_modal = 0
    if "modal_content" not in st.session_state:
        st.session_state.modal_content = ""
        
    return modal

# --- Sample Data for Mock LLM ---
def load_sample_data():
    """Load sample documents for the mock LLM."""
    # Sample documents
    sample_docs = [
        {'id': '0', 'text': 'Emperor penguins are the tallest.', 'title': 'Tall penguins'},
        {'id': '3', 'text': 'Yusuf is an AI student', 'title': 'AI student'},
        {'id': '4', 'text': 'Yusuf studies at La Sapienza University', 'title': 'AI student home University name'},
        {'id': '5', 'text': 'He is currently doing an Erasmus Programme in Trento University', 'title': 'AI student host University location'},
        {'id': '6', 'text': 'La Sapienza is a university located in Rome in the Lazio region of Italy. Trento university, instead, is located in Trento in Italy', 'title': 'Location of Home University and Host University'}
    ]

    # Store documents in session state for access in the dialog
    docs_dict = {doc['id']: doc for doc in sample_docs}
    
    # Sample text with citations
    sample_text = """
    I'm doing well, thanks for asking.
    The tallest living penguins are [citation:0]{Emperor penguins}.
    Yusuf is an [citation:3]{AI student} who studies at [citation:4]{La Sapienza University}. 
    His host university, [citation:5]{Trento University}, is located in [citation:6]{Trento, Italy}.
    """
    
    return sample_docs, docs_dict, sample_text

# --- Utility Functions ---
def get_current_datetime():
    """Returns formatted current date and time."""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M")

def get_model_name():
    """Returns the model name."""
    return "Gemma 3"

def find_url_in_text(text):
    """Finds the first http/https URL in a string."""
    # Simple regex for finding URLs
    urls = re.findall(r'https?://\S+', text)
    return urls[0] if urls else None

def extract_citations(text):
    """Extracts citations in the format [citation:id]{content} from text."""
    pattern = r'\[citation:([^\]]+)\]\{([^}]+)\}'
    matches = re.findall(pattern, text)
    citations = {citation_id: content for citation_id, content in matches}
    return citations

def format_text_with_citations(text, citations):
    """Replaces citation tags with HTML spans that can be clicked to trigger citation display."""
    def citation_replacement(match):
        citation_id = match.group(1)
        cited_text = match.group(2)
        unique_key = f"citation-{citation_id}-{uuid.uuid4().hex[:8]}"
        
        # Create a span with styling for the citation
        return f'''
                <span 
                class="citation" 
                id="{unique_key}" 
                data-key="{unique_key}"
                data-citation-id="{citation_id}" 
                style="background-color: #ADD8E6; color: black; padding: 2px 4px; border-radius: 3px; border-bottom: 2px dashed #007bff; cursor: pointer;"
                onclick="document.getElementById('trigger-button-{citation_id}').click();">
                {escape(cited_text)}[{citation_id}]
            </span>
            
            <script language="javascript">
            document.querySelector("span").style.color = "red";
            </script>
            '''
    
    # Replace all citation tags with styled spans
    pattern = r'\[citation:([^\]]+)\]\{([^}]+)\}'
    formatted_text = re.sub(pattern, citation_replacement, text)
    
    return formatted_text

def get_mock_llm_response(user_message):
    """Simulates an LLM response, sometimes includes a link."""
    if "penguin" in user_message.lower():
        return sample_docs[0]['text']
    elif "ai" in user_message.lower():
        return sample_docs[1]['text']
    elif "home" in user_message.lower() or "sapienza" in user_message.lower():
        return sample_docs[2]['text']
    elif "host" in user_message.lower() or "trento" in user_message.lower():
        return sample_docs[3]['text']
    elif "location" in user_message.lower():
        return sample_docs[4]['text']
    elif "sample" in user_message.lower():
        return sample_text 
    else:
        return f"Write another of the words: [penguin, ai, home, host, sapienza, trento, location]"

# --- Chat Management Functions ---
def create_new_chat():
    """Create a new chat session and set it as current."""
    new_chat_id = str(uuid.uuid4())
    st.session_state.chat_sessions[new_chat_id] = {
        "title": f"Chat {len(st.session_state.chat_sessions) + 1}",
        "messages": []
    }
    st.session_state.current_chat_id = new_chat_id

def switch_to_chat(chat_id):
    """Switch to a different chat session."""
    st.session_state.current_chat_id = chat_id

def add_user_message(chat_id, content):
    """Add a user message to the specified chat session."""
    st.session_state.chat_sessions[chat_id]["messages"].append({
        "role": "user", 
        "content": content
    })

def add_assistant_message(chat_id, content):
    """Add an assistant message to the specified chat session."""
    found_url = find_url_in_text(content)
    
    st.session_state.chat_sessions[chat_id]["messages"].append({
        "role": "assistant",
        "content": content,
        "datetime": get_current_datetime(),
        "ai_model": get_model_name(),
        "link": found_url  # Store the link with the message
    })

def process_user_input(user_input):
    """Process user input and generate response."""
    if not user_input or not st.session_state.current_chat_id:
        return
    
    # Add user message
    add_user_message(st.session_state.current_chat_id, user_input)
    
    # Get and add assistant response
    llm_response = get_mock_llm_response(user_input)
    add_assistant_message(st.session_state.current_chat_id, llm_response)

# --- UI Rendering Functions ---
def render_header():
    """Render the app header."""
    st.header(":blue[Nature4AI] :sunglasses:", divider=True)

def render_sidebar():
    """Render the sidebar with chat sessions."""
    with st.sidebar:
        # Sidebar header
        chat_list_container = st.container()
        with chat_list_container:
            col_settings, col_profile, _, col_new_chat, _ = st.columns([0.60, 0.15, 0.05, 0.15, 0.05])
            with col_settings:
                if st.button("Settinigs"):
                    st.write("Settings cliccked")
            with col_profile:
                if st.button(f"{st.session_state.user_profile['avatar']}"):
                    st.write(f"User clicked")
            with col_new_chat:
                # Button to start a new chat
                if st.button("➕"):
                    create_new_chat()
                    st.rerun()  # Rerun to update the main view

        # Display list of existing chats
        if not st.session_state.chat_sessions:
            st.caption("No chats yet.")
        else:
            # Scrollable Chat List
            chat_list_container = st.container(height=300, border=True)
            with chat_list_container:
                st.header("Chat Sessions", divider=True)
                # Sort chats by title for consistency
                sorted_chat_ids = sorted(st.session_state.chat_sessions.keys(), reverse=True,
                                        key=lambda k: st.session_state.chat_sessions[k]['title'])

                for chat_id in sorted_chat_ids:
                    chat_title = st.session_state.chat_sessions[chat_id]['title']
                    button_type = "primary" if chat_id == st.session_state.current_chat_id else "secondary"
                    if st.button(f"💬 {chat_title[:30]}", key=f"chat_{chat_id}", use_container_width=True, type=button_type):
                        switch_to_chat(chat_id)
                        st.rerun()  # Only reload main content when switching chats

def render_chat_message(message, index):
    """Render a single chat message."""
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # Process message content to handle citations
            content = message["content"]
            
            # Display content
            st.markdown(content)
            
            # Citations handling
            citations = extract_citations(sample_text)
            formatted_text = format_text_with_citations(sample_text, citations)
            st.markdown("(Click on highlighted text to view citation details)")
            components.html(formatted_text)
            
            # Citation buttons
            cols = st.columns(len(citations))
            for idx, citation_id in enumerate(citations.keys()):
                with cols[idx]:
                    if st.button(f"[{citation_id}]", key=f"{index}_{idx}", help="Click to view citation details"):
                        st.session_state.open_modal = citation_id
                        st.session_state.modal_content = f"citation-{citation_id}"
                        modal.open()
            
            # Add timestamp and AI model info
            st.caption(f"{message.get('datetime', get_current_datetime())} | {message.get('ai_model', get_model_name())}")
        else:
            # Display user message normally
            st.markdown(message["content"])

def render_chat_area():
    """Render the main chat area."""
    chat_container = st.container()  # Use a container for better control

    if st.session_state.current_chat_id:
        current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]

        with chat_container:
            # Display chat messages
            for i, message in enumerate(current_chat["messages"]):
                render_chat_message(message, i)

            st.divider()  # Separator before input

        # Chat input at the bottom
        user_input = st.chat_input("Type your message here...")

        if user_input:
            process_user_input(user_input)
            # Only rerun to display the new message, not the entire app
            st.rerun()

    else:
        with chat_container:
            st.info("Select a chat from the sidebar or start a new one.")

def render_citation_modal(modal_content):
    """Render citation details in a modal."""
    with modal.container():
        chat_list_container = st.container(height=400, border=True)
        with chat_list_container:
            st.write("Text goes here")

            html_string = f'''
            <h1>HTML string in RED with open modal id: {st.session_state.open_modal}</h1>
            
            {modal_content}

            <script language="javascript">
            document.querySelector("h1").style.color = "red";
            </script>
            '''
            components.html(html_string)

            st.write("Some fancy text")
            value = st.checkbox("Check me")
            st.write(f"Checkbox checked: {value}")

def add_custom_css():
    """Add custom CSS for styling."""
    st.markdown("""
    <style>
    .citation:hover {
        background-color: #7FB3D5 !important;
        transition: background-color 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Dialog Function ---
@st.dialog("Citation Details")
def display_citation_dialog(citation_id, docs_dict):
    """Display citation details in a dialog."""
    # Get the document for this citation ID
    doc = docs_dict[citation_id]
    st.markdown(f"## {doc['title']}")
    st.markdown(f"**Document ID:** {doc['id']}")
    st.markdown(f"**Content:** {doc['text']}")
    
    # Add a close button
    if st.button("Close"):
        st.rerun()

# --- Main Application ---
def main():
    # Initialize app
    global modal, sample_docs, docs_dict, sample_text
    modal = initialize_app()
    sample_docs, docs_dict, sample_text = load_sample_data()
    
    # Add custom CSS
    add_custom_css()
    
    # Render UI components
    render_header()
    render_sidebar()
    render_chat_area()
    
    # Handle modal display
    if modal.is_open():
        render_citation_modal(st.session_state.modal_content)

if __name__ == "__main__":
    main()