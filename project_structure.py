import os

# Define the folder and file structures
structure = {
    "chatbot_project": {
        
        # FastAPI app
        "backend": {
            "api": ["chat.py", "citation.py", "sessions.py", "__init__.py"], #  ← API routes and logic
            "core": ["llm.py", "vectorstore.py", "chat_engine.py", "__init__.py"], #  ← Core logic (LLM, vector store, etc.)
            "db": ["models.py", "crud.py", "database.py", "__init__.py"], # ← DB models and operations
            "main.py": None, # ← Entry point for FastAPI server
            "requirements.txt": None
        },
        
        # Streamlit or other frontend
        "frontend": {
            "components": ["__init__.py"], # ← Reusable UI components
            "assets": [], # CSS, images, etc.
            "main.py": None, # ← Streamlit UI logic
            "utils.py": None # ← Frontend utilities
        },
        "notebooks": ["test1.ipynb"], #  ← Jupyter notebooks for testing and exploration
        # "scripts": ["ingest_docs.py", "test_vectorstore.py"], #  ← Setup, training, indexing scripts
        # ".env": None, # ← Secrets and config
        # "README.md": None,
        # "pyproject.toml": None
    }
}

def create_structure(base_path, struct):
    for name, content in struct.items():
        path = os.path.join(base_path, name)
        if content is None:
            open(path, 'a').close()  # Create empty file
        else:
            os.makedirs(path, exist_ok=True)
            if isinstance(content, list):
                for filename in content:
                    open(os.path.join(path, filename), 'a').close()
            elif isinstance(content, dict):
                create_structure(path, content)

if __name__ == "__main__":
    base_dir = "."  # Create in current directory
    create_structure(base_dir, structure["chatbot_project"])
    print("✅ Project structure created successfully.")
