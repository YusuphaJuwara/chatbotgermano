import os
import typing as tp
from tqdm import tqdm
from core.vectorstore import Vectorstore
from db.mysql_v1 import MYSQL
import cohere
from cohere.types.chat_citation import ChatCitation

import logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv('.env')
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

class Chatbot:
    
    def __init__(self, vectorstore: Vectorstore):
        """
        Initialize the Chatbot with a vectorstore and a language model (LLM).
        
        Parameters:
        - vectorstore: The vector store for document retrieval.
        - llm: The language model for generating responses.
        """
        self.vectorstore = vectorstore
        self.llm = cohere.Client(COHERE_API_KEY) # Get your API key here: https://dashboard.cohere.com/api-keys
        self.chat_history: list = []
        
    def new_chat(self, message: str):
        """
        Start a new chat session with the given message.
        
        Parameters:
        - message: The initial message from the user.
        """
        self.chat_history = []
        self.chat(message)

    def chat(self, message: str):
        """
        1. Give the user message to the LLM to determine if additional context is needed
        2. If so:
        - The LLM returns search queries
        - We retrieve the documents from the DB,
        - The LLM uses the documents as context and responds
        3. If not:
        - The LLM responds directly without additional context
        """

        # Generate search queries, if any
        query_prompt = "Generate 3 search queries for this user message so that I can optimally search a database. \nUser Message: "
        response = self.llm.chat(message = query_prompt + message,
                            model="command-a-03-2025",
                            search_queries_only=True, # Generate only search queries, not full responses
                            chat_history=self.chat_history)
        # print(f"\n\n{'##'*20}\nSearch queries:\n{'##'*20}\n")
        search_queries = []
        for query in response.search_queries:
            search_queries.append(query.text)

        # If there are search queries, retrieve the documents
        if search_queries:
            logger.info("Retrieving information...")

            # Retrieve document chunks for each query
            documents = []
            for query in search_queries:
                documents.extend(self.vectorstore.retrieve(query))
            print(f"Documents that matched the query: \n{documents}")

            # Use document chunks to respond
            response = self.llm.chat_stream(
                message=message,
                model="command-a-03-2025",
                documents=documents,
                chat_history=self.chat_history,
            )

        else:
            # If no additional context is needed, respond directly
            docs = self.vectorstore.retrieve(message)
            response = self.llm.chat_stream(
                message=message,
                model="command-a-03-2025",
                documents=docs,
                chat_history=self.chat_history,
            )

        # Print the chatbot response and citations
        chatbot_response = ""
        citations: tp.List[ChatCitation] = []
        documents: tp.List[dict] = []
        # print(f"\n\n{'##'*20}\nChatbot:\n{'##'*20}\n")

        for event in response:
            if event.event_type == "text-generation":
                # print(event.text, end="")
                chatbot_response += event.text
            if event.event_type == "stream-end":
                if event.response.citations:
                    # citations.extend(event.response.citations)
                    # print(f"Type event.response.citations: {type(event.response.citations)}")
                    # print(f"Length of event.response.citations: {len(event.response.citations)}")
                    # print(f"Type : {type(event.response.citations[0])}")
                    # print("\n\nCITATIONS:")
                    for citation in event.response.citations:
                        citations.append(citation.dict())
                    #     print(citation)
                if event.response.documents:
                    documents.extend(event.response.documents)
                    # print(f"Type event.response.documents: {type(event.response.documents)}")
                    # print(f"Length of event.response.documents: {len(event.response.documents)}")
                    # print(f"Type : {type(event.response.documents[0])} \t Keys: {event.response.documents[0].keys()}")
                    # print("\nCITED DOCUMENTS:")
                    # for document in event.response.documents:
                    #     print(document)
                # Update the chat history for the next turn
                self.chat_history = event.response.chat_history
                
        return chatbot_response, citations, documents

if __name__ == "__main__":
    
    logger.setLevel(logging.ERROR)
    
    # Initialize the vector store and LLM
    db_faq = "ecommerce_faq"
    MYSQL.create_and_init_db(db_faq)  # Run once to create the database and tables
    engine = MYSQL.get_db_connection(db_faq)
    faq_data = MYSQL.load_faq_data()
    logger.info(f"\n{'##'*20}\nFAQ data:\n{'##'*20} \n{faq_data}\n")

    # Create the vector store
    vectorstore = Vectorstore(docs=faq_data)

    # Initialize the chatbot
    chatbot = Chatbot(vectorstore=vectorstore)

    # Start a chat session
    # chatbot.chat("Hi, can I ask questions?")
    chatbot_response, citations, documents = chatbot.chat("What is the return policy?")
    print(f"\n\n{'##'*20}\nChatbot:\n{'##'*20}\n{chatbot_response}")
    print(f"\n\n{'##'*20}\nCitations:\n{'##'*20}\n{citations}")
    print(f"\n\n{'##'*20}\nDocuments:\n{'##'*20}\n{documents}")
    # chatbot.chat("Ok, thanks! But what if I couldn't return an item on time?")
    
    # # # Reset the chat session and start a new one
    # chatbot.new_chat("Which payment methods are accepted?")
    