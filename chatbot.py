from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from config import CONFIG
from document_processor import DocumentProcessor
from langchain.memory.buffer_window import ConversationBufferWindowMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_core.retrievers import BaseRetriever
from typing import List, Dict, Any, Optional
import streamlit as st
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class ChatBot:
    """Main chatbot class that handles conversations and document queries"""
    def __init__(self, document_processor: DocumentProcessor):
        logger.info("Initializing ChatBot")
        self.llm = ChatGroq(
            groq_api_key=CONFIG["GROQ_API_KEY"],
            model=CONFIG["MODEL_NAME"],
            temperature=CONFIG["TEMPERATURE"],
        )
        self.document_processor = document_processor
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
            k=5  # Keep last 5 exchanges
        )
        logger.debug("Initialized conversation memory")
        self.qa_chain = None
        self.setup_qa_chain()
    
    def setup_qa_chain(self):
        """Setup the conversational retrieval chain"""
        logger.info("Setting up QA chain")
        vector_store = self.document_processor.get_vector_store()
        
        if vector_store:
            logger.debug("Vector store available, creating QA chain")
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
                memory=self.memory,
                return_source_documents=True,
                output_key="answer",
                verbose=True,

            )
            logger.info("QA chain initialized successfully")
        else:
            logger.warning("No vector store available for QA chain setup")

    
    def detect_call_request(self, message: str) -> bool:
        """Detect if user is requesting a call/appointment"""
        logger.debug(f"Detecting call request in message: {message[:50]}...")
        call_keywords = [
            'call me', 'call back', 'schedule call', 'book appointment',
            'appointment', 'meeting', 'talk to someone', 'speak with',
            'contact me', 'get in touch', 'schedule meeting'
        ]
        
        message_lower = message.lower()
        detected = any(keyword in message_lower for keyword in call_keywords)
        logger.debug(f"Call request detected: {detected}")
        return detected
    

    def get_response(self, message: str, chat_history: List[Dict]) -> Dict[str, Any]:
        """Get response from the chatbot with improved logic"""
        logger.info(f"Processing message: {message[:100]}...")
        
        # Don't process call requests here - let tool agents handle them
        # This prevents random tool activation
        
        # Use QA chain if available and not a call request
        if self.qa_chain and not self.detect_call_request(message):
            try:
                logger.debug("Using QA chain for response")
                formatted_history = self._format_chat_history(chat_history)
                
                result = self.qa_chain({
                    "question": message,
                    "chat_history": formatted_history
                })
                
                logger.debug("QA chain response generated")
                return {
                    "response": result["answer"],
                    "requires_form": False,
                    "source_documents": result.get("source_documents", [])
                }
                
            except Exception as e:
                logger.error(f"QA chain error: {str(e)}", exc_info=True)
                # Fall through to direct LLM response
        
        # Fallback to direct LLM response
        try:
            logger.debug("Using direct LLM response")
            prompt = self._create_prompt(message, chat_history)
            response = self.llm.invoke(prompt)
            
            return {
                "response": response.content,
                "requires_form": False,
                "source_documents": []
            }
            
        except Exception as e:
            logger.error(f"Direct LLM error: {str(e)}", exc_info=True)
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "requires_form": False,
                "source_documents": []
            }


    
    def _create_prompt(self, message: str, chat_history: List[Dict]) -> str:
        """Create a prompt for direct LLM response"""
        logger.debug("Creating fallback prompt")
        context = ""
        if chat_history:
            recent_history = chat_history[-3:]  # Last 3 exchanges
            logger.debug(f"Using {len(recent_history)} history items for context")
            for chat in recent_history:
                role = "Human" if chat["role"] == "user" else "Assistant"
                context += f"{role}: {chat['content']}\n"
        
        prompt = f"""You are a helpful assistant. Based on the conversation context below, please provide a helpful and accurate response.

                Context:
                {context}

                Current question: {message}

                Please provide a helpful response:"""
        logger.debug(f"Constructed prompt length: {len(prompt)} characters")
        
        return prompt

    def update_documents(self):
        """Update the QA chain when new documents are added"""
        logger.info("Updating documents and resetting QA chain")
        self.setup_qa_chain()
    
    def _format_chat_history(self, chat_history: List[Dict]) -> List[tuple]:
        """Format chat history for the chain"""
        logger.debug("Formatting chat history")
        formatted_history = []
        for chat in chat_history[-5:]:  # Keep last 5 exchanges
            if chat["role"] == "user":
                user_msg = chat["content"]
            elif chat["role"] == "assistant":
                assistant_msg = chat["content"]
                if user_msg and assistant_msg:
                    formatted_history.append((user_msg, assistant_msg))
                    user_msg = None
                    assistant_msg = None
        logger.debug(f"Formatted history contains {len(formatted_history)} QA pairs")
        return formatted_history