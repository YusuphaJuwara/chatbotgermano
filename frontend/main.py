import datetime
import os
import streamlit as st
import streamlit.components.v1 as components
from streamlit_modal import Modal

# -----------------------------------------------------------------------
# Page Configuration must come first
# -----------------------------------------------------------------------
st.set_page_config(
    layout="centered",
    page_title="Chat App",
    page_icon="🤖",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': '# Streamlit Chat with FastAPI Backend!'
    },
)

# -----------------------------------------------------------------------
# Ensure a valid BACKEND_URL is set (never None)
# -----------------------------------------------------------------------
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
_raw_url = os.getenv("BACKEND_URL", "").strip()

if _raw_url:
    BACKEND_URL = _raw_url
else:
    BACKEND_URL = f"http://localhost:{BACKEND_PORT}"

# Guarantee scheme
if not BACKEND_URL.startswith(("http://", "https://")):
    BACKEND_URL = "http://" + BACKEND_URL

# For debugging: expose the URL in the query params using new API
st.set_query_params(debug_backend=BACKEND_URL)
print(f"▶️ Using BACKEND_URL = {BACKEND_URL}")

# Inject into utils so all api_... functions use this base
import utils
utils.BACKEND_URL = BACKEND_URL

# Now import API helper functions
from utils import (
    handle_api_error,
    api_get_sessions,
    api_create_session,
    api_get_messages,
    api_create_message,
    api_get_citation,
    api_get_docs,
    get_model_name_from_message,
    extract_citations,
    format_text_with_citations,
)

# -----------------------------------------------------------------------
# Initialization
# -----------------------------------------------------------------------
def initialize_app():
    """Initialize session_state and fetch initial chat sessions."""
    if "chat_sessions" not in st.session_state:
        sessions = api_get_sessions()
        if sessions is None:
            st.error(f"Could not reach backend at {BACKEND_URL}/sessions/")
            st.stop()
        st.session_state.chat_sessions = {s['id']: s for s in sessions}

    # Default session state keys
    defaults = {
        'current_chat_id': None,
        'messages': [],
        'show_citation_id': None,
        'documents_cache': {},
        'user_profile': {'name': 'User', 'avatar': '👤'}
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Create modal instance for citations
    modal = Modal(
        title="Citation Details",
        key="citation-modal",
        padding=20,
        max_width=700
    )
    return modal

# -----------------------------------------------------------------------
# UI Rendering Functions
# -----------------------------------------------------------------------
def render_header():
    st.header(":blue[Nature4AI Chat (FastAPI)] :recycle:", divider=True)


def render_sidebar():
    with st.sidebar:
        col_settings, col_profile, _, col_new_chat, _ = st.columns([0.6, 0.15, 0.05, 0.15, 0.05])
        with col_settings:
            if st.button("Settings", key="settings_btn"):
                st.toast("Settings clicked (placeholder)")
        with col_profile:
            if st.button(st.session_state.user_profile['avatar'], key="profile_btn"):
                st.toast("Profile clicked")
        with col_new_chat:
            if st.button("➕", key="new_chat_btn"):
                with st.spinner("Creating new chat..."):
                    new_sess = api_create_session()
                if new_sess:
                    st.session_state.chat_sessions[new_sess['id']] = new_sess
                    st.session_state.current_chat_id = new_sess['id']
                    st.session_state.messages = []
                    st.session_state.show_citation_id = None
                    st.session_state.documents_cache = {}
                    st.toast(f"Created '{new_sess['title']}'")
                    st.rerun()
                else:
                    st.error("Failed to create new chat session.")

        st.divider()
        st.header("Chat Sessions", divider=False)
        if not st.session_state.chat_sessions:
            st.caption("No chats yet. Click ➕ to start!")
        else:
            cont = st.container(height=300, border=True)
            with cont:
                for chat_id, sess in st.session_state.chat_sessions.items():
                    title = sess.get('title', chat_id[:6])
                    btn_type = "primary" if chat_id == st.session_state.current_chat_id else "secondary"
                    if st.button(f"💬 {title}", key=f"chat_{chat_id}", type=btn_type, use_container_width=True):
                        if st.session_state.current_chat_id != chat_id:
                            st.session_state.current_chat_id = chat_id
                            st.session_state.messages = []
                            st.session_state.show_citation_id = None
                            st.session_state.documents_cache = {}
                            with st.spinner(f"Loading '{title}'..."):
                                msgs = api_get_messages(chat_id)
                            if msgs is not None:
                                st.session_state.messages = msgs
                            else:
                                st.error("Failed to load messages.")
                            st.rerun()


def render_chat_message(message: dict, idx: int):
    model = get_model_name_from_message(message) if message['role'] == 'assistant' else None
    with st.chat_message(message['role']):
        content = message.get('content', '')
        cites = message.get('citations', [])
        out = format_text_with_citations(content, cites) if cites else content
        st.markdown(out, unsafe_allow_html=True)
        if cites:
            cols = st.columns(len(cites))
            for i, c in enumerate(cites):
                with cols[i]:
                    cid = c['id']
                    if st.button(f"[{cid}]", key=f"cit_{cid}_{idx}"):
                        st.session_state.show_citation_id = cid
                        st.rerun()
        ts = message.get('timestamp', '')
        if isinstance(ts, datetime.datetime):
            ts = ts.strftime("%Y-%m-%d %H:%M")
        st.caption(" | ".join(filter(None, [ts, model or ''])))
        link = message.get('link')
        if link and st.button("🔗 View Link", key=f"link_{idx}"):
            components.html(f"<script>window.open('{link}','_blank')</script>", height=0, width=0)


def render_chat_area():
    cont = st.container(height=500)
    with cont:
        if not st.session_state.current_chat_id:
            st.info("Select or create a chat.")
        else:
            if not st.session_state.messages:
                st.caption("No messages yet.")
            for i, msg in enumerate(st.session_state.messages):
                render_chat_message(msg, i)
    if st.session_state.current_chat_id:
        st.divider()
        user_input = st.chat_input("Type your message...")
        if user_input:
            cid = st.session_state.current_chat_id
            with st.spinner("Sending..."):
                res = api_create_message(cid, 'user', user_input)
            if res:
                with st.spinner("Refreshing..."):
                    msgs = api_get_messages(cid)
                if msgs:
                    st.session_state.messages = msgs
                st.rerun()
            else:
                st.error("Failed to send message.")


def display_citation_modal(modal: Modal):
    cid = st.session_state.show_citation_id
    if cid and not modal.is_open():
        modal.open()
    if modal.is_open() and cid:
        docs = st.session_state.documents_cache.get(cid)
        if not docs:
            with st.spinner("Loading citation..."):
                ids = api_get_citation(cid)
                docs = api_get_docs(ids) if ids else None
            if docs:
                st.session_state.documents_cache[cid] = docs
        with modal.container():
            if docs:
                for d in docs:
                    st.markdown(f"### {d.get('title')}")

