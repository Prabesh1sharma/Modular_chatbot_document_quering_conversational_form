import os
import weaviate
from weaviate.auth import AuthApiKey
from langchain_community.vectorstores import Weaviate  # Changed from FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from config import CONFIG
import streamlit as st
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import Docx2txtLoader
import logging
import shutil

# Initialize logger
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document loading, processing, and vector store creation"""
    def __init__(self):
        logger.info("Initializing DocumentProcessor")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=CONFIG["EMBEDDING_MODEL"],
            model_kwargs={"device": "cpu"}
        )
        logger.debug(f"Loaded embeddings model: {CONFIG['EMBEDDING_MODEL']}")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONFIG["CHUNK_SIZE"],
            chunk_overlap=CONFIG["CHUNK_OVERLAP"]
        )
        logger.debug(f"Initialized text splitter with chunk size {CONFIG['CHUNK_SIZE']}, overlap {CONFIG['CHUNK_OVERLAP']}")
        
        # Initialize Weaviate client using v3 style for LangChain compatibility
        self.weaviate_client = weaviate.Client(
            url="http://localhost:8080"
        )
        self.index_name = "DocumentIndex"
        self.vector_store = None
        self.load_vector_store()
        
    def load_documents(self, file_paths: List[str]) -> List[Document]:
        """Load documents from file paths"""
        logger.info(f"Loading documents from {len(file_paths)} files")
        documents = []
        
        for file_path in file_paths:
            try:
                logger.debug(f"Processing file: {file_path}")
                if file_path.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                    logger.debug("Initialized PDF loader")
                elif file_path.endswith('.txt'):
                    loader = TextLoader(file_path)
                    logger.debug("Initialized Text loader")
                elif file_path.endswith('.docx'):
                    loader = Docx2txtLoader(file_path)
                    logger.debug("Initialized DOCX loader")
                else:
                    logger.warning(f"Unsupported file type: {file_path}")
                    st.warning(f"Unsupported file type: {file_path}")
                    continue
                
                docs = loader.load()
                logger.info(f"Loaded {len(docs)} documents from {file_path}")
                documents.extend(docs)
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {str(e)}", exc_info=True)
                print(f"DEBUG: Error loading {file_path}:{str(e)} ")
                st.error(f"Error loading {file_path}: {str(e)}")
        
        return documents
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        logger.info("Processing documents into chunks")
        if not documents:
            logger.warning("No documents received for processing")
            return []
        
        chunks = self.text_splitter.split_documents(documents)
        logger.debug(f"Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks
    
    def clear_vector_store(self):
        """Clear existing vector store data"""
        logger.info("Clearing existing vector store data")
        try:
            # Delete the collection if it exists using v3 API
            if self.weaviate_client.schema.exists(self.index_name):
                self.weaviate_client.schema.delete_class(self.index_name)
                logger.info(f"Deleted existing Weaviate collection: {self.index_name}")
            
            # Reset the vector store instance
            self.vector_store = None
            logger.info("Vector store cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}", exc_info=True)
            print(f"DEBUG: Error clearing vector store: {str(e)}")
            st.error(f"Error clearing vector store: {str(e)}")
    
    def create_vector_store(self, documents: List[Document]) -> Weaviate:  # Changed return type
        """Create new vector store from documents (replaces existing one)"""
        logger.info("Creating new vector store (replacing existing)")
        if not documents:
            logger.error("No documents provided for vector store creation")
            return None
        
        # Clear existing vector store first
        self.clear_vector_store()
        
        chunks = self.process_documents(documents)
        logger.info(f"Creating new vector store from {len(chunks)} chunks")
        try:
            # Always create a new vector store (no merging)
            logger.debug("Creating brand new vector store")
            self.vector_store = Weaviate.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                client=self.weaviate_client,
                index_name=self.index_name,
                text_key="text"
            )
            logger.info(f"Created new vector store with {len(chunks)} chunks")
            
            self.save_vector_store()
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Vector store creation failed: {str(e)}", exc_info=True)
            print(f"DEBUG: Error creating vector store {str(e)} ")
            st.error(f"Error creating vector store: {str(e)}")
            return None
    
    def save_vector_store(self):
        """Save vector store to disk"""
        if self.vector_store:
            logger.info(f"Saving vector store to Weaviate")
            try:
                # Weaviate automatically persists data, no explicit save needed
                logger.info("Vector store saved successfully (Weaviate auto-persists)")
                st.success("Vector store created and saved successfully!")
            except Exception as e:
                logger.error(f"Error saving vector store: {str(e)}", exc_info=True)
                print(f"DEBUG: Error saving vector store {str(e)} ")
                st.error(f"Error saving vector store: {str(e)}")
    
    def load_vector_store(self):
        """Load vector store from disk"""
        try:
            logger.info(f"Loading vector store from Weaviate")
            if self.weaviate_client.schema.exists(self.index_name):
                self.vector_store = Weaviate(
                    client=self.weaviate_client,
                    index_name=self.index_name,
                    text_key="text",
                    embedding=self.embeddings
                )
                logger.info("Vector store loaded successfully")
                st.session_state.vector_store_loaded = True
            else:
                logger.warning("No existing Weaviate collection found")
                self.vector_store = None
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}", exc_info=True)
            print(f"DEBUG: Error occur in load_vector_store {str(e)} ")
            st.warning(f" NO vector store loaded please load it:")
            self.vector_store = None
    
    def search_documents(self, query: str, k: int = 4) -> List[Document]:
        """Search for relevant documents"""
        logger.info(f"Document search initiated: {query[:50]}... (k={k})")
        if not self.vector_store:
            logger.warning("Search attempted with no vector store available")
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            logger.debug(f"Found {len(docs)} relevant documents")
            return docs
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            print(f"DEBUG: Error searching document : {str(e)} ")
            st.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_vector_store(self) -> Optional[Weaviate]:  # Changed return type
        """Get the current vector store"""
        logger.debug(f"Vector store requested. Available: {self.vector_store is not None}")
        return self.vector_store
