import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import LlamaCpp
from langchain.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)

# Database connection
def get_db_connection(database_name):
    server = os.getenv("SQL_SERVER", "HUAWEI-MIRKO")
    username = os.getenv("SQL_USERNAME", "tarta")
    password = os.getenv("SQL_PASSWORD", "")
    connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server"
    return create_engine(connection_string)

# Initialize HuggingFace embeddings for vector storage
model_name = "EleutherAI/gpt-j-6B"  # Smaller, faster model good for Windows
embeddings = HuggingFaceEmbeddings(model_name=model_name)

# Initialize Llama model using llama.cpp (optimized for CPU usage on Windows)
def initialize_llm():
    model_name = "EleutherAI/gpt-j-6B"  # You can switch to "EleutherAI/gpt-neo-2.7B" for a smaller model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32)

    def llm(prompt):
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
        outputs = model.generate(**inputs, max_new_tokens=300, do_sample=True, temperature=0.7)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    return llm

# Load FAQ data and create vector store
def load_faq_data():
    engine = get_db_connection("ecommerce_faq")
    query = "SELECT question, answer FROM faq_table"
    
    with engine.connect() as connection:
        result = connection.execute(text(query))
        rows = result.fetchall()
    
    documents = []
    for row in rows:
        documents.append(f"Question: {row[0]}\nAnswer: {row[1]}")
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.create_documents([doc for doc in documents])
    
    # Using persist_directory to save the vectorstore for reuse
    return Chroma.from_documents(
        documents=texts, 
        embedding=embeddings, 
        persist_directory="./chroma_db/faq"
    )

# Load ticketing data and create vector store
def load_ticketing_data():
    engine = get_db_connection("ecommerce_ticketing")
    query = "SELECT ticket_id, customer_query, resolution FROM tickets WHERE status = 'resolved'"
    
    with engine.connect() as connection:
        result = connection.execute(text(query))
        rows = result.fetchall()
    
    documents = []
    for row in rows:
        documents.append(f"Ticket: {row[0]}\nQuery: {row[1]}\nResolution: {row[2]}")
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.create_documents([doc for doc in documents])
    
    # Using persist_directory to save the vectorstore for reuse
    return Chroma.from_documents(
        documents=texts, 
        embedding=embeddings, 
        persist_directory="./chroma_db/tickets"
    )

# Initialize or load knowledge bases
def init_knowledge_bases():
    # Check if vectorstores already exist and load them if they do
    if os.path.exists("./chroma_db/faq") and os.path.exists("./chroma_db/tickets"):
        faq_vectorstore = Chroma(persist_directory="./chroma_db/faq", embedding_function=embeddings)
        ticketing_vectorstore = Chroma(persist_directory="./chroma_db/tickets", embedding_function=embeddings)
    else:
        # Create directories if they don't exist
        os.makedirs("./chroma_db/faq", exist_ok=True)
        os.makedirs("./chroma_db/tickets", exist_ok=True)
        
        faq_vectorstore = load_faq_data()
        ticketing_vectorstore = load_ticketing_data()
        
        # Persist the vector stores
        faq_vectorstore.persist()
        ticketing_vectorstore.persist()
    
    return faq_vectorstore, ticketing_vectorstore

# Combine retrieval from both vector stores
def get_combined_retriever(faq_vectorstore, ticketing_vectorstore):
    faq_retriever = faq_vectorstore.as_retriever(search_kwargs={"k": 2})
    ticketing_retriever = ticketing_vectorstore.as_retriever(search_kwargs={"k": 2})
    
    class CombinedRetriever:
        def get_relevant_documents(self, query):
            faq_docs = faq_retriever.get_relevant_documents(query)
            ticket_docs = ticketing_retriever.get_relevant_documents(query)
            return faq_docs + ticket_docs
    
    return CombinedRetriever()

# Direct QA approach (more efficient for Windows machines)
def direct_qa(query, faq_vectorstore, ticketing_vectorstore, llm):
    # Get relevant documents
    combined_retriever = get_combined_retriever(faq_vectorstore, ticketing_vectorstore)
    relevant_docs = combined_retriever.get_relevant_documents(query)
    
    # Format context from documents
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    
    # Create prompt in Llama 3 instruct format
    prompt = f"""<|begin_of_text|><|system|>
You are a helpful e-commerce customer support assistant. Answer the customer question based only on the provided information.
If you don't know the answer, say so politely and suggest contacting human support.

Information:
{context}
<|user|>
{query}
<|assistant|>"""
    
    # Get response from model
    response = llm(prompt)
    
    return response.strip()

# Record interaction in database
def record_interaction(session_id, user_message, bot_response):
    engine = get_db_connection("ecommerce_ticketing")
    
    # Insert conversation into a tracking table for future model improvement
    query = text("""
    INSERT INTO conversation_history (session_id, user_message, bot_response, timestamp)
    VALUES (:session_id, :user_message, :bot_response, GETDATE())
    """)
    
    with engine.connect() as connection:
        connection.execute(query, {
            "session_id": session_id,
            "user_message": user_message,
            "bot_response": bot_response
        })
        connection.commit()

# Initialize app
llm = initialize_llm()
faq_vectorstore, ticketing_vectorstore = init_knowledge_bases()

# API routes
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    if 'message' not in data:
        return jsonify({"error": "No message provided"}), 400
    
    user_message = data['message']
    session_id = data.get('session_id', 'default')
    
    # Using the more efficient direct QA approach (better for Windows)
    answer = direct_qa(user_message, faq_vectorstore, ticketing_vectorstore, llm)
    
    # Record interaction in the database for future learning
    try:
        record_interaction(session_id, user_message, answer)
    except Exception as e:
        print(f"Error recording interaction: {e}")
    
    return jsonify({
        "response": answer,
        "session_id": session_id
    })

@app.route('/api/feedback', methods=['POST'])
def feedback():
    data = request.json
    if not all(k in data for k in ('session_id', 'message_id', 'rating')):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Record feedback for model improvement
    engine = get_db_connection("ecommerce_ticketing")
    
    query = text("""
    INSERT INTO feedback (session_id, message_id, rating, comment, timestamp)
    VALUES (:session_id, :message_id, :rating, :comment, GETDATE())
    """)
    
    with engine.connect() as connection:
        connection.execute(query, {
            "session_id": data['session_id'],
            "message_id": data['message_id'],
            "rating": data['rating'],
            "comment": data.get('comment', '')
        })
        connection.commit()
    
    return jsonify({"status": "success"})

# Route for retraining the model with new data
@app.route('/api/retrain', methods=['POST'])
def retrain():
    global faq_vectorstore, ticketing_vectorstore
    
    faq_vectorstore = load_faq_data()
    ticketing_vectorstore = load_ticketing_data()
    
    # Persist the updated vector stores
    faq_vectorstore.persist()
    ticketing_vectorstore.persist()
    
    return jsonify({"status": "success", "message": "Knowledge base updated with latest data"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)