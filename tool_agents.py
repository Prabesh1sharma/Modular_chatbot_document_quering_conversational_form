from typing import Dict, Any, List, Optional
import streamlit as st
from conversational_form import ConversationalForm
from validators import DateExtractor
from config import CONFIG
import json
from datetime import datetime
from langchain_groq import ChatGroq
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent

from langchain_core.tools import Tool
from langchain.agents.react.agent import create_react_agent
import logging
import re
from langchain_core.prompts import PromptTemplate
 
# Initialize logger
logger = logging.getLogger(__name__)


class ToolAgents:
    """Handles tool-based agents for specialized tasks"""
    
    def __init__(self, conversational_form: ConversationalForm):
        logger.info("Initializing ToolAgents")
        self.llm = ChatGroq(
            groq_api_key=CONFIG["GROQ_API_KEY"],
            model=CONFIG["MODEL_NAME"],
            temperature=CONFIG["TEMPERATURE"],
        )
        self.conversational_form = conversational_form
        self.date_extractor = DateExtractor()
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        
        def schedule_appointment_tool(input_text: str) -> str:
            """Tool to handle appointment scheduling requests"""
            logger.info("schedule_appointment_tool called")
            try:
                # Initialize form if not already active
                if not self.conversational_form.is_form_active():
                    logger.debug("Form not active, initializing form")
                    result = self.conversational_form.initialize_form()
                    return result["response"]
                else:
                    # Process current form input
                    logger.debug("Form active, processing input")
                    result = self.conversational_form.process_form_input(input_text)
                    return result["response"]
            except Exception as e:
                logger.error(f"Error processing appointment request: {str(e)}", exc_info=True)
                print(f"DEBUG: Error process appointment request :{str(e)} ")

                return f"Error processing appointment request: {str(e)}"
        
        def extract_date_tool(date_text: str) -> str:
            """Tool to extract and normalize dates from natural language"""
            logger.info("extract_date_tool called")
            try:
                extracted_date = self.date_extractor.extract_date(date_text)
                if extracted_date:
                    date_obj = datetime.strptime(extracted_date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%A, %B %d, %Y")
                    logger.debug(f"Extracted date: {extracted_date} ({formatted_date})")
                    return f"Extracted date: {extracted_date} ({formatted_date})"
                else:
                    logger.warning("Could not extract a valid date from the input")
                    return "Could not extract a valid date from the input"
            except Exception as e:
                logger.error(f"Error extracting date: {str(e)}", exc_info=True)
                print(f"DEBUG: Error extracting datta :{str(e)} ")
                return f"Error extracting date: {str(e)}"
        
        def get_form_status_tool(input_text: str) -> str:
            """Tool to get current form collection status"""
            logger.info("get_form_status_tool called")
            try:
                if self.conversational_form.is_form_active():
                    progress = self.conversational_form.get_form_progress()
                    current_step = self.conversational_form.get_current_step()
                    form_data = st.session_state.get("form_data", {})
                    
                    status = {
                        "active": True,
                        "progress": progress,
                        "current_step": current_step,
                        "collected_data": list(form_data.keys())
                    }
                    logger.debug(f"Form status: {status}")
                    return json.dumps(status, indent=2)
                else:
                    logger.debug("No form collection in progress")
                    return json.dumps({"active": False, "message": "No form collection in progress"})
            except Exception as e:
                logger.error(f"Error getting form status: {str(e)}", exc_info=True)
                print(f"DEBUG: Error getting form status :{str(e)} ")
                return f"Error getting form status: {str(e)}"
        
        def validate_contact_info_tool(contact_info: str) -> str:
            """Tool to validate contact information (email, phone)"""
            logger.info("validate_contact_info_tool called")
            try:
                from validators import FormValidator
                validator = FormValidator()
                
                # Try to detect what type of contact info this is
                if "@" in contact_info:
                    is_valid, message = validator.validate_email(contact_info)
                    logger.debug(f"Email validation: {message}")
                    return f"Email validation: {message}"
                elif any(char.isdigit() for char in contact_info):
                    is_valid, message = validator.validate_phone(contact_info)
                    logger.debug(f"Phone validation: {message}")
                    return f"Phone validation: {message}"
                else:
                    logger.warning("Unable to determine contact info type")
                    return "Unable to determine contact info type. Please provide email or phone number."
            except Exception as e:
                logger.error(f"Error validating contact info: {str(e)}", exc_info=True)
                print(f"DEBUG: Error validating contact infor :{str(e)} ")
                return f"Error validating contact info: {str(e)}"
        
        def get_completed_appointments_tool(input_text: str) -> str:
            """Tool to retrieve completed appointments"""
            logger.info("get_completed_appointments_tool called")
            try:
                completed_forms = st.session_state.get("completed_forms", [])
                if not completed_forms:
                    logger.info("No completed appointments found")
                    return "No completed appointments found."
                
                appointments_info = []
                for i, form in enumerate(completed_forms[-5:], 1):  # Last 5 appointments
                    appointment = {
                        "number": i,
                        "name": form.get("name", "N/A"),
                        "email": form.get("email", "N/A"),
                        "phone": form.get("phone", "N/A"),
                        "date": form.get("formatted_date", form.get("date", "N/A")),
                        "requested": form.get("timestamp", "N/A")[:19] if form.get("timestamp") else "N/A"
                    }
                    appointments_info.append(appointment)
                logger.debug(f"Returning {len(appointments_info)} completed appointments")
                
                return json.dumps({"appointments": appointments_info}, indent=2)
            except Exception as e:
                logger.error(f"Error retrieving appointments: {str(e)}", exc_info=True)
                print(f"DEBUG: Error retrieving appointments :{str(e)} ")
                return f"Error retrieving appointments: {str(e)}"

        return [
            Tool(
                name="schedule_appointment",
                description="Use this tool when user wants to schedule a call, book an appointment, or provide contact information during form collection. Input should be the user's message.",
                func=schedule_appointment_tool
            ),
            Tool(
                name="extract_date",
                description="Use this tool to extract and normalize dates from natural language input like 'tomorrow', 'next Monday', or specific dates.",
                func=extract_date_tool
            ),
            Tool(
                name="get_form_status",
                description="Use this tool to check the current status of form collection process.",
                func=get_form_status_tool
            ),
            Tool(
                name="validate_contact_info",
                description="Use this tool to validate email addresses or phone numbers.",
                func=validate_contact_info_tool
            ),
            Tool(
                name="get_completed_appointments",
                description="Use this tool to retrieve information about completed appointments.",
                func=get_completed_appointments_tool
            )
        ]
    
    def _create_agent(self) -> Optional[AgentExecutor]:
        """Create the ReAct agent with tools"""
        logger.info("Creating ReAct agent with tools")
        try:
            # Get the ReAct prompt from hub
            prompt = self._create_custom_prompt()
            
            # Create the agent
            agent = create_tool_calling_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            agent_executor = AgentExecutor(
                # llm = self.llm,
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15
            )
            logger.info("Agent executor created successfully")
            return agent_executor
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            print(f"DEBUG: Error creating agent :{str(e)} ")
            st.error(f"Error creating agent: {str(e)}")
            return None
    
    def should_use_agent(self, user_input: str) -> bool:
        """Determine if we should use the agent for this input - more precise triggers"""
        logger.debug(f"Checking if agent should be used for input: {user_input[:50]}...")
        
        # If form is already active, always use agent
        if self.conversational_form.is_form_active():
            logger.debug("Form is active, using agent")
            return True
        
        # More specific appointment/scheduling keywords
        appointment_triggers = [
            'call me', 'call back', 'schedule call', 'book appointment',
            'appointment', 'meeting', 'talk to someone', 'speak with',
            'contact me', 'get in touch', 'schedule meeting'
        ]
        
        user_input_lower = user_input.lower().strip()
        
        # Check for exact phrase matches or patterns
        for trigger in appointment_triggers:
            if trigger in user_input_lower:
                logger.debug(f"Appointment trigger matched: {trigger}")
                return True
        
        # Check for direct appointment requests with context
        appointment_patterns = [
            r'\b(can you|could you|please)\s+(call|contact)\s+me\b',
            r'\b(schedule|book)\s+(a|an)?\s*(call|appointment|meeting)\b',
            r'\bi\s*(want|need|would like)\s+(to\s+)?(schedule|book)\b'
        ]
        
        for pattern in appointment_patterns:
            if re.search(pattern, user_input_lower):
                logger.debug(f"Appointment pattern matched: {pattern}")
                return True
        
        logger.debug("No agent triggers found")
        return False

    
    def process_with_agent(self, user_input: str) -> Dict[str, Any]:
        """Process user input using the agent"""
        logger.info(f"Processing input with agent: {user_input[:50]}...")
        try:
            if not self.agent:
                logger.warning("Agent not available")
                return {
                    "response": "Agent is not available. Please try again later.",
                    "tool_used": None,
                    "success": False
                }
            
            # If form is active, always use the appointment tool
            if self.conversational_form.is_form_active():
                logger.debug("Form is active, using schedule_appointment tool")
                result = self.conversational_form.process_form_input(user_input)
                return {
                    "response": result["response"],
                    "tool_used": "schedule_appointment",
                    "success": True,
                    "form_completed": result.get("form_completed", False)
                }
            logger.debug("Invoking agent for input")
            # Use agent to process the input
            result = self.agent.invoke({
                "input": user_input,
                "chat_history": ""
            })
            logger.info("Agent processed input successfully")
            return {
                "response": result["output"],
                "tool_used": "agent",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing user request: {str(e)}", exc_info=True)
            print(f"DEBUG: Error user request :{str(e)} ")
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            
            # Fallback: if it looks like an appointment request, try to handle it directly
            if any(keyword in user_input.lower() for keyword in ['call', 'appointment', 'schedule', 'book']):
                try:
                    logger.debug("Fallback: initializing form due to error")
                    result = self.conversational_form.initialize_form()
                    return {
                        "response": result["response"],
                        "tool_used": "schedule_appointment_fallback",
                        "success": True
                    }
                except Exception as inner_e:
                    logger.error(f"Error in fallback form initialization: {str(inner_e)}", exc_info=True)
            
            return {
                "response": error_msg,
                "tool_used": None,
                "success": False
            }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        logger.debug("Getting available tool names")
        return [tool.name for tool in self.tools]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools"""
        return {tool.name: tool.description for tool in self.tools}
    
    def reset_agent_state(self):
        """Reset any persistent agent state if needed"""
        logger.info("Resetting agent state")
        try:
            # Reset form state if needed
            if hasattr(self, 'conversational_form'):
                st.session_state.collecting_form = False
                st.session_state.form_step = None
                st.session_state.form_data = {}
        except Exception as e:
            logger.error(f"Error resetting agent state: {str(e)}", exc_info=True)
            print(f"DEBUG: Error resetting agent states :{str(e)} ")
            st.error(f"Error resetting agent state: {str(e)}")
    
    def _create_custom_prompt(self) -> PromptTemplate:
        """Create a simple, focused prompt for appointment scheduling"""
        template = """You are an appointment scheduling assistant. Help users book calls by collecting their contact information.

    Available tools: {tools}
    Tool names: [{tool_names}]

    Rules:
    1. Use schedule_appointment tool ONLY when user wants to book a call OR  and then intialize with form and get the response of it 
    2. Use extract_date tool ONLY for parsing dates during scheduling
    3. For general questions, respond directly without using tools
    4. Never accept fake data like "John Doe" or "test@example.com"

    Format:
    Question: {input}
    Thought: [analyze if tools are needed]
    Action: [tool name or skip if no tool needed]
    Action Input: [user's message]
    First Response: [Response with tool result]
    Observation: [tool result]
    Final Answer: [response to user]

    Question: {input}
    Thought:{agent_scratchpad}"""

        return PromptTemplate.from_template(template)
