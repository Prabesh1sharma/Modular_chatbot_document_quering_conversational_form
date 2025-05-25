# AI Document Chatbot with Appointment Booking

A comprehensive chatbot system built with Streamlit, LangChain, and Groq that can answer questions from uploaded documents and collect user information through conversational forms for appointment booking.

## 🌟 Features

### Document Q&A
- **Multi-format Support**: Upload PDF, TXT, and DOCX files
- **Intelligent Chunking**: Documents are split into optimal chunks for better retrieval
- **Vector Search**: Uses FAISS for efficient similarity search
- **Conversational Memory**: Maintains context across conversations
- **Source Citations**: Shows relevant document sections for answers

### Appointment Booking System
- **Natural Language Processing**: Understands requests like "call me" or "book appointment"
- **Conversational Forms**: Step-by-step information collection
- **Smart Date Extraction**: Handles natural date inputs like "next Monday", "tomorrow"
- **Input Validation**: Real-time validation for emails, phone numbers, and names
- **Confirmation Process**: Users can review and confirm their information

### Tool Integration
- **Agent-based Architecture**: Uses LangChain agents for specialized tasks
- **Multiple Tools**: Date extraction, validation, form management, and search
- **Context Awareness**: Switches between document Q&A and form collection seamlessly

## 📁 Project Structure

```
├── app.py                    # Main Streamlit application
├── config.py                # Configuration settings
├── document_processor.py     # Document loading and vector store management
├── chatbot.py               # Main chatbot logic
├── conversational_form.py   # Form collection and management
├── tool_agents.py           # Agent tools and integration
├── validators.py            # Input validation and date extraction
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Installation

1. **Clone or download all the files to a directory**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Groq API key:**
   - Get your API key from [Groq Console](https://console.groq.com/)
   - Either set it as an environment variable as creating .env and inside .env  set this:
     ```bash
     GROQ_API_KEY=your-api-key-here
     ```
   - Or enter it directly in the app's sidebar when you run it

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## 🔧 Configuration

Edit `config.py` to customize:

- **MODEL_NAME**: Groq model to use (default: "llama-3.3-70b-versatile2")
- **CHUNK_SIZE**: Document chunk size (default: 1000)
- **CHUNK_OVERLAP**: Overlap between chunks (default: 200)
- **TEMPERATURE**: Model creativity (default: 0.3)
- **MAX_TOKENs**:  (default: 4000)
- **EMBEDDING_MODEL**: Sentence transformer model (default: "sentence-transformers/all-mpnet-base-v2")

## 📖 Usage Guide

### Document Q&A

1. **Upload Documents:**
   - Use the sidebar to upload PDF, TXT, or DOCX files
   - Click "Process Documents" to create the vector store
   - Documents are chunked and indexed automatically

2. **Ask Questions:**
   - Type questions about your documents in the chat
   - Get answers with relevant source excerpts
   - Maintain conversation context

### Appointment Booking

1. **Trigger Form Collection:**
   - Say things like "call me", "book appointment", "schedule a meeting"
   - The system will detect the intent and start form collection

2. **Provide Information:**
   - **Name**: Full name validation
   - **Email**: Email format validation
   - **Phone**: phone number validation
   - **Date**: Natural language date parsing (e.g., "next Monday", "tomorrow")

3. **Confirmation:**
   - Review your information
   - Confirm or request changes
   - Receive confirmation message

### Natural Date Input Examples

The system understands various date formats:
- "tomorrow", "today", "yesterday"
- "next Monday", "next Friday"
- "next week", "next month"
- "2024-01-15", "01/15/2024"
- "January 15th", "Jan 15"

## 🛠️ Available Tools

The system includes several specialized tools:

1. **schedule_appointment**: Handles appointment booking workflow
2. **extract_date**: Converts natural language to YYYY-MM-DD format
3. **get_form_status**: Shows current form collection progress
4. **validate_contact_info**: Validates emails, phones, and names
5. **search_appointments**: Searches through completed appointments

## 🎨 Features in Detail

### Validation System
- **Email**: Verifying Email with regex
- **Phone**: Character validation and length requirements of Phone numbers
- **Name**: Character validation and length requirements
- **Date**: Comprehensive natural language date parsing

### Conversational Flow
- **Context Switching**: Seamlessly switches between document Q&A and form collection
- **Memory Management**: Maintains conversation history and form state
- **Error Handling**: Graceful error recovery with helpful messages
- **Progress Tracking**: Shows form completion progress

### User Interface
- **Clean Design**: Intuitive Streamlit interface
- **Sidebar Organization**: Document upload, form status, and help sections
- **Chat History**: Persistent conversation display
- **Real-time Updates**: Dynamic form progress and status updates

## 🔒 Security & Privacy

- **No Persistent Storage**: Forms are only stored in session state
- **API Key Security**: Keys are handled securely through environment variables
- **Input Sanitization**: All user inputs are validated and sanitized
- **Error Boundaries**: Comprehensive error handling prevents crashes

## 🚨 Troubleshooting

### Common Issues

1. **"Agent is not available"**
   - Check your Groq API key
   - Ensure internet connectivity
   - Verify model availability

2. **Document processing fails**
   - Check file format (PDF, TXT, DOCX only)
   - Ensure files are not corrupted
   - Check file size limitations

3. **Faiss Issue**
   - Check if the faiss is installed correctly
### Performance Tips

- **Document Size**: Keep documents under 10MB for best performance
- **Chunk Size**: Adjust chunk size based on document complexity
- **Memory Usage**: Clear chat history periodically for long sessions
- **API Limits**: Monitor Groq API usage to avoid rate limits

