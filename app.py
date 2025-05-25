import streamlit as st
import os
from typing import List, Dict
import traceback
import re
# Import our custom modules
from config import CONFIG
from document_processor import DocumentProcessor
from chatbot import ChatBot
from conversational_form import ConversationalForm
from tool_agents import ToolAgents
import logging
from datetime import datetime
import logging



if not logging.getLogger().handlers:
    os.makedirs("logs", exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"logs/{timestamp}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Document Chatbot with Appointment Booking",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    .user-message {
        background-color: #0000FF;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #000000;
        margin-right: 2rem;
    }
    .form-progress {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "document_processor" not in st.session_state:
        st.session_state.document_processor = DocumentProcessor()
    
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = ChatBot(st.session_state.document_processor)
    
    if "conversational_form" not in st.session_state:
        st.session_state.conversational_form = ConversationalForm()
    
    if "tool_agents" not in st.session_state:
        st.session_state.tool_agents = ToolAgents(st.session_state.conversational_form)
    
    if "collecting_form" not in st.session_state:
        st.session_state.collecting_form = False
    
    if "completed_forms" not in st.session_state:
        st.session_state.completed_forms = []



def display_document_upload():
    """Enhanced document upload with better validation and state management"""
    with st.sidebar:
        st.subheader("📄 Document Upload")
        
        # Initialize session state variables if they don't exist
        if "vector_store_loaded" not in st.session_state:
            st.session_state.vector_store_loaded = False
        if "document_processor" not in st.session_state:
            st.error("Document processor not initialized. Please restart the application.")
            return
        
        # Check current vector store status more reliably
        vector_store_exists = False
        if hasattr(st.session_state, 'document_processor'):
            vector_store = st.session_state.document_processor.get_vector_store()
            vector_store_exists = vector_store is not None
            
            # Sync the session state with actual vector store status
            st.session_state.vector_store_loaded = vector_store_exists
        
        # Display current status with more detailed information
        if vector_store_exists:
            st.success("✅ Vector store loaded and ready")
            
            # Show additional info if available
            try:
                if hasattr(st.session_state.document_processor.vector_store, 'index'):
                    doc_count = st.session_state.document_processor.vector_store.index.ntotal
                    st.info(f"📊 {doc_count} document chunks indexed")
            except Exception as e:
                logger.debug(f"Could not get document count: {e}")
                
            # Add clear vector store option
            if st.button("🗑️ Clear Vector Store", help="Remove all loaded documents"):
                with st.spinner("Clearing vector store..."):
                    try:
                        st.session_state.document_processor.clear_vector_store()
                        st.session_state.vector_store_loaded = False
                        st.success("Vector store cleared successfully!")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error clearing vector store: {str(e)}")
                        st.error(f"Error clearing vector store: {str(e)}")
        else:
            st.warning("⚠️ No documents loaded yet")
            st.info("Upload documents below to start chatting about them")
        
        st.divider()
        
        # File upload section
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['pdf', 'txt', 'docx'],
            accept_multiple_files=True,
            help="Supported formats: PDF, TXT, DOCX (max 50MB total recommended)",
            key="document_uploader"
        )
        
        if uploaded_files:
            # Validate files and show detailed info
            st.write("**📋 Files ready for processing:**")
            valid_files = []
            total_size = 0
            
            for i, file in enumerate(uploaded_files, 1):
                try:
                    size_bytes = len(file.getvalue())
                    size_mb = size_bytes / (1024 * 1024)
                    total_size += size_mb
                    
                    # File validation
                    if size_mb > 25:  # Individual file size limit
                        st.error(f"❌ {file.name} is too large ({size_mb:.1f} MB). Max 25MB per file.")
                        continue
                    
                    if size_bytes == 0:
                        st.error(f"❌ {file.name} is empty.")
                        continue
                    
                    valid_files.append(file)
                    
                    # Display file info with status
                    status_icon = "✅" if size_mb < 10 else "⚠️"
                    st.write(f"{status_icon} **{i}.** {file.name} ({size_mb:.1f} MB)")
                    
                except Exception as e:
                    logger.error(f"Error validating file {file.name}: {str(e)}")
                    st.error(f"❌ Error reading {file.name}: {str(e)}")
            
            # Show total size and warnings
            if total_size > 50:
                st.warning(f"⚠️ Total size: {total_size:.1f} MB. Large files may take longer to process.")
            elif total_size > 0:
                st.info(f"📊 Total size: {total_size:.1f} MB")
            
            # Process button - only show if there are valid files
            if valid_files:
                process_button_text = "🚀 Process Documents" if not vector_store_exists else "🔄 Replace Existing Documents"
                process_help = "This will replace any existing documents" if vector_store_exists else "Create vector store from uploaded documents"
                
                if st.button(process_button_text, type="primary", help=process_help, use_container_width=True):
                    process_documents(valid_files)
            else:
                st.error("❌ No valid files to process")
        
        # Add helpful information
        with st.expander("ℹ️ Upload Guidelines"):
            st.markdown("""
            **Supported Formats:**
            - 📄 PDF files (.pdf)
            - 📝 Text files (.txt)
            - 📄 Word documents (.docx)
            
            **Best Practices:**
            - Keep individual files under 25MB
            - Ensure text is readable (not scanned images)
            - Use descriptive filenames
            - Check files open correctly before uploading
            
            **Processing Notes:**
            - Documents are split into chunks for better search
            - Existing documents will be replaced when uploading new ones
            - Processing time depends on file size and content
            """)

def process_documents(uploaded_files):
    """Process uploaded documents with comprehensive error handling and user feedback"""
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Setup (10%)
        status_text.text("🔧 Setting up processing...")
        progress_bar.progress(10)
        
        # Ensure upload directory exists
        upload_dir = CONFIG.get("UPLOADED_DOCS_PATH", "uploaded_docs")
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Upload directory ready: {upload_dir}")
        
        # Step 2: Save files (30%)
        status_text.text("💾 Saving uploaded files...")
        progress_bar.progress(30)
        
        file_paths = []
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                file_path = os.path.join(upload_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(file_path)
                logger.info(f"Saved file: {file_path}")
                
                # Update progress for each file
                step_progress = 30 + (20 * (i + 1) / len(uploaded_files))
                progress_bar.progress(int(step_progress))
                
            except Exception as e:
                logger.error(f"Error saving file {uploaded_file.name}: {str(e)}")
                st.error(f"❌ Failed to save {uploaded_file.name}: {str(e)}")
                return False
        
        # Step 3: Load documents (60%)
        status_text.text("📖 Loading and parsing documents...")
        progress_bar.progress(60)
        
        if not hasattr(st.session_state, 'document_processor'):
            st.error("❌ Document processor not available. Please restart the application.")
            return False
        
        documents = st.session_state.document_processor.load_documents(file_paths)
        
        if not documents:
            st.error("❌ No valid documents were loaded. Please check your files and try again.")
            return False
        
        logger.info(f"Successfully loaded {len(documents)} document sections")
        
        # Step 4: Create vector store (80%)
        status_text.text("🔍 Creating searchable index...")
        progress_bar.progress(80)
        
        vector_store = st.session_state.document_processor.create_vector_store(documents)
        
        if not vector_store:
            st.error("❌ Failed to create vector store. Please try again.")
            return False
        
        # Step 5: Finalize (100%)
        status_text.text("✅ Finalizing setup...")
        progress_bar.progress(100)
        
        # Update chatbot if available
        if hasattr(st.session_state, 'chatbot'):
            try:
                st.session_state.chatbot.update_documents()
                logger.info("Chatbot updated with new documents")
            except Exception as e:
                logger.warning(f"Could not update chatbot: {str(e)}")
        
        # Update session state
        st.session_state.vector_store_loaded = True
        
        # Success message
        st.success(f"🎉 Successfully processed {len(documents)} document sections from {len(uploaded_files)} files!")
        
        # Clean up progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Auto-rerun to update UI
        st.rerun()
        
        return True
        
    except Exception as e:
        error_msg = f"Unexpected error during processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(f"❌ {error_msg}")
        
        # Clean up progress indicators on error
        progress_bar.empty()
        status_text.empty()
        
        return False
    
    finally:
        # Cleanup uploaded files if needed (optional)
        try:
            if 'file_paths' in locals():
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not clean up temporary files: {str(e)}")


def display_form_status():
    """Display current form collection status"""
    if st.session_state.conversational_form.is_form_active():
        with st.sidebar:
            st.subheader("📋 Form Collection Status")
            progress = st.session_state.conversational_form.get_form_progress()
            st.info(f"**{progress}**")
            
            # Show collected data so far
            form_data = st.session_state.get("form_data", {})
            if form_data:
                st.write("**Collected Information:**")
                for key, value in form_data.items():
                    if key != "formatted_date":  # Don't show duplicate date info
                        st.write(f"• **{key.title()}:** {value}")

def display_completed_appointments():
    """Display completed appointments in sidebar"""
    completed_forms = st.session_state.get("completed_forms", [])
    if completed_forms:
        with st.sidebar:
            st.subheader("✅ Recent Appointments")
            
            for i, form in enumerate(completed_forms[-3:]):  # Show last 3
                with st.expander(f"Appointment {i+1}: {form['name']}"):
                    st.write(f"**Email:** {form['email']}")
                    st.write(f"**Phone:** {form['phone']}")
                    st.write(f"**Date:** {form.get('formatted_date', form['date'])}")
                    st.write(f"**Requested:** {form['timestamp'][:19]}")

def display_chat_messages():
    """Display chat messages"""
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>Assistant:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)

def process_user_input(user_input: str):
    """Process user input with better routing logic"""
    if not user_input.strip():
        return
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    try:
        # Determine processing method
        should_use_agent = (
            st.session_state.tool_agents.should_use_agent(user_input) or 
            st.session_state.conversational_form.is_form_active()
        )
        
        if should_use_agent:
            logger.info("Using tool agents for processing")
            result = st.session_state.tool_agents.process_with_agent(user_input)
            response = result["response"]
            
        else:
            logger.info("Using regular chatbot for processing")
            result = st.session_state.chatbot.get_response(
                user_input, 
                st.session_state.messages[:-1]
            )
            response = result["response"]
            
            # Display source documents if available
            if result.get("source_documents"):
                with st.expander("📚 Source Documents"):
                    for i, doc in enumerate(result["source_documents"]):
                        st.write(f"**Source {i+1}:**")
                        st.write(doc.page_content[:200] + "...")
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        
    except Exception as e:
        logger.error(f"Error processing user input: {str(e)}", exc_info=True)
        error_msg = "I apologize, but I encountered an error processing your request. Please try again."
        st.session_state.messages.append({"role": "assistant", "content": error_msg})


def main():
    """Main application function"""
    st.title("🤖 AI Document Chatbot with Appointment Booking")
    st.markdown("Upload documents to chat about them, or ask me to schedule a call!")
    
    # Initialize session state
    initialize_session_state()
    # Display sidebar components
    display_document_upload()
    display_form_status()
    display_completed_appointments()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("💬 Chat")
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            display_chat_messages()
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            process_user_input(user_input)
            st.rerun()
    
    with col2:
        st.subheader("ℹ️ Help")
        
        st.markdown("""
        **What can I do?**
        
        📚 **Document Q&A:**
        - Upload PDF, TXT, or DOCX files
        - Ask questions about your documents
        - Get relevant answers with sources
        
        📞 **Appointment Booking:**
        - Say "call me" or "book appointment"
        - I'll collect your contact information
        - Supports natural date input like "next Monday"
        
        🛠️ **Smart Tools:**
        - Date extraction and validation
        - Contact information validation
        - Form management and tracking
        
        **Example Queries:**
        - "What is this document about?"
        - "Schedule a call for tomorrow"
        - "Book an appointment for next Friday"
        - "Can you call me back?"
        """)
        
        # Display tool information
        if st.session_state.tool_agents:
            with st.expander("🔧 Available Tools"):
                tools = st.session_state.tool_agents.get_available_tools()
                for tool in tools:
                    st.write(f"• {tool}")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.session_state.collecting_form = False
            st.session_state.form_step = None
            st.session_state.form_data = {}
            st.rerun()

if __name__ == "__main__":
    main()