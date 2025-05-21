"""# --- API Client Functions ---"""

import os
import datetime
import re
from typing import List
# import uuid
from html import escape
import streamlit as st
import requests # Import requests for API calls

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv('.env')

# --- Configuration ---
BACKEND_PORT = os.getenv("BACKEND_PORT") # Port for the backend API (default: 8000)
BACKEND_URL = os.getenv("BACKEND_URL") #"http://localhost:8000" # Or http://127.0.0.1:8000

def handle_api_error(response: requests.Response, context: str) -> None:
    """This function handles the error response from the API responses and displays it in the Streamlit app.
    It tries to parse the JSON response and extract the error message, or falls back to the raw text.
    
    Args:
        response (requests.Response): The response object from the API call.
        context (str): A string describing the context of the API call (e.g., "fetching sessions").
        
    Returns:
        None: Returns None to indicate an error occurred.
    """
    try:
        detail = response.json().get("detail", response.text)
    except requests.exceptions.JSONDecodeError:
        detail = response.text
    st.error(f"API Error ({context}): {response.status_code} - {detail}")
    return None

def api_get_sessions() -> List[dict]:
    """This function handles the API call to the backend and returns a list of session dictionaries.
    It handles errors and network issues gracefully, displaying appropriate messages in the Streamlit app.
    
    Returns:
        List[dict]: A list of session dictionaries, or an empty list if an error occurred.
    """
    try:
        logger.info(f"Fetching sessions from {BACKEND_URL}/sessions/")
        response = requests.get(f"{BACKEND_URL}/sessions/")
        logger.info(f"Response: {response}")
        if response.status_code == 200:
            return response.json() # Returns list of session dicts
        else:
            handle_api_error(response, "fetching sessions")
            return [] # Return empty list on error
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching sessions: {e}")
        return []

def api_create_session(title: str = None) -> dict:
    """Create a new chat session via the backend.
    
    Args:
        title (str): Optional title for the session.
        
    Returns:
        dict: The created session dictionary, or None if an error occurred.
    """
    payload = {}
    if title:
        payload["title"] = title
    try:
        response = requests.post(f"{BACKEND_URL}/sessions/", json=payload)
        if response.status_code == 201: # Created
            return response.json() # Return the new session dict
        else:
            handle_api_error(response, "creating session")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error creating session: {e}")
        return None

def api_get_messages(session_id: str) -> List[dict]:
    """Fetch messages for a specific session.
    
    Args:
        session_id (str): The ID of the session to fetch messages for.
        
    Returns:
        List[dict]: A list of message dictionaries, or an empty list if an error occurred.
    """
    if not session_id: return []
    try:
        response = requests.get(f"{BACKEND_URL}/sessions/{session_id}/messages/")
        if response.status_code == 200:
            # Convert timestamp strings to datetime objects if necessary (FastAPI/Pydantic might do this)
            messages = response.json()
            for msg in messages:
                 if isinstance(msg.get("timestamp"), str):
                     try:
                         # Attempt to parse ISO format timestamp
                         msg["timestamp"] = datetime.datetime.fromisoformat(msg["timestamp"])
                     except ValueError:
                          # Handle other potential formats or leave as string if parsing fails
                          pass # Keep original string if parsing fails
            return messages # Returns list of message dicts
        elif response.status_code == 404:
             st.warning(f"Session {session_id} not found on backend.")
             return []
        else:
            handle_api_error(response, f"fetching messages for session {session_id}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching messages: {e}")
        return []

def api_create_message(
    session_id: str, role: str, content: str, ai_model: str = None, link: str = None
    ) -> dict:
    """Post a new message to the backend and get the Assistant response with possible citations.
    
    Args:
        session_id (str): The ID of the session to post the message to.
        role (str): The role of the message sender ('user' or 'assistant').
        content (str): The content of the message.
        ai_model (str, optional): The AI model used for the message (if applicable).
        link (str, optional): An optional URL associated with the message. TODO: remove link
        
    Returns:
        dict: The assistant message dictionary, or None if an error occurred.
    """
    if not session_id: return None
    payload = {"role": role, "content": content}
    if ai_model:
        payload["ai_model"] = ai_model
    if link:
        payload["link"] = link

    try:
        response = requests.post(f"{BACKEND_URL}/sessions/{session_id}/messages/", json=payload)
        if response.status_code == 201: # Created
            return response.json() # Return the created message dict
        else:
            handle_api_error(response, "creating message")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error creating message: {e}")
        return None

def api_get_citation(citation_id: str) -> List[str]:
    """Fetch document ids from the backend associated with the citation id.
    
    Args:
        citation_id (str): The ID of the citation for which to fetch the document ids.
        
    Returns:
        List[str]: A list of document IDs associated with the citation, or None if an error occurred.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/citations/{citation_id}")
        if response.status_code == 200:
            response_json = response.json() # Returns citation dict {'id', 'title', 'text'}
            doc_ids = response_json['doc_ids']
            return doc_ids
        elif response.status_code == 404:
             st.toast(f"Citation '{citation_id}' not found.")
             return None
        else:
            handle_api_error(response, f"fetching citation {citation_id}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching citation: {e}")
        return None
    
def api_get_docs(doc_ids: List[str]) -> List[dict]:
    """Fetch documents from the backend.
    
    Args:
        doc_ids (List[str]): A list of document IDs to fetch.
        
    Returns:
        List[dict]: A list of document dictionaries, or None if an error occurred.
    """
    try:
        response = requests.post(f"{BACKEND_URL}/sessions/documents/", json={"doc_ids": doc_ids})
        if response.status_code == 200:
            return response.json() # Returns docs dict {'id', 'text', etc.}
        elif response.status_code == 404:
             st.toast(f"Documents '{doc_ids}' not found.")
             return None
        else:
            handle_api_error(response, f"fetching citation {doc_ids}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching citation: {e}")
        return None
    

# --- Modified Utility Functions ---

def get_model_name_from_message(message: dict) -> str:
    """Gets the model name from the message data, or provides a default."""
    return message.get("ai_model", "Gemma3") # Use model from backend if available

def find_url_in_text(text):
    """TODO: Remove
    Finds the first http/https URL in a string. """
    urls = re.findall(r'https?://\S+', text)
    return urls[0] if urls else None

def extract_citations(text):
    """TODO: Remove
    Extracts citations in the format [citation:id]{content} from text. (Unchanged)"""
    pattern = r'\[citation:([^\]]+)\]\{([^}]+)\}'
    matches = re.findall(pattern, text)
    # Return dict {citation_id: content}
    return {citation_id: content for citation_id, content in matches}

def format_text_with_citations(text: str, citations: List[dict]) -> str:
    """Highlights with HTML the part of the assistant response where that was cited.

    Args:
        text (str): The text to format.
        citations (List[dict]): A list of citation dictionaries, each containing 'id', 'text', 'start', and 'end', etc.

    Returns:
        str: The formatted text with citations replaced by HTML spans.
    """
    # Sort citations by their start index in descending order
    # This is crucial to avoid issues with shifting indices when replacing
    citations.sort(key=lambda c: c['start'], reverse=True)

    for citation in citations:
        citation_id = citation['id']
        start = citation['start']
        end = citation['end']
        
        # Extract the exact text from the original 'text' string based on start and end
        # This ensures we're replacing the correct part of the original string
        original_cited_text = text[start:end]

        # Create a span with the citation ID and text
        span_html = f'<span class="citation" data-citation-id="{citation_id}" style="background-color: #ADD8E6; color: black; padding: 2px 4px; border-radius: 3px; border-bottom: 2px dashed #007bff; cursor: pointer;">{escape(original_cited_text)}[{citation_id}]</span>'

        # Reconstruct the string by inserting the span at the correct position
        text = text[:start] + span_html + text[end:]
        
    return text
    
def format_text_with_citations2(text):
    """TODO: Remove
    Replaces citation tags with HTML spans that trigger citation display via button click."""
    def citation_replacement(match):
        citation_id = match.group(1)
        cited_text = match.group(2)
        # Unique key for the *invisible button* - needs instance info if in loop
        # We'll add instance info (like message index) in render_chat_message
        button_base_id = f"trigger-button-{citation_id}"

        # The visible span - onclick triggers button associated with this specific citation instance
        # The actual button ID will be dynamically created where this is used.
        span_html = f'''
            <span
                class="citation"
                data-citation-id="{citation_id}"
                style="background-color: #ADD8E6; color: black; padding: 2px 4px; border-radius: 3px; border-bottom: 2px dashed #007bff; cursor: pointer;"
                onclick="
                    var buttons = document.querySelectorAll('button[id^=\\'{button_base_id}\\']');
                    if (buttons.length > 0) {{ buttons[0].click(); }} else {{ console.error('Button {button_base_id} not found'); }}
                    event.stopPropagation(); // Prevent potential parent clicks
                "
                title="Click to view citation '{citation_id}'"
            >
                {escape(cited_text)}[{citation_id}]
            </span>'''
        return span_html
    
    pattern = r'\[citation:([^\]]+)\]\{([^}]+)\}'
    formatted_text = re.sub(pattern, citation_replacement, text, flags=re.DOTALL) # Handle multiline content
    return formatted_text