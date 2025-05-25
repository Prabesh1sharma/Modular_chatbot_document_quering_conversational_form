import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
from validators import FormValidator, DateExtractor
import logging
logger = logging.getLogger(__name__)

class ConversationalForm:
    """Handles conversational form collection for user information"""
    def __init__(self):
        self.validator = FormValidator()
        self.date_extractor = DateExtractor()
        self.form_steps = [
            "name",
            "email", 
            "phone",
            "date",
            "confirmation"
        ]
        logger.debug("Initialized ConversationalForm with steps: %s", self.form_steps)


    def get_current_step(self) -> str:
        """Get the current form step"""
        logger.debug("Current form step: %s", st.session_state.get("form_step", "name"))
        return st.session_state.get("form_step", "name")
    
    def get_next_step(self, current_step: str) -> Optional[str]:
        """Get the next step in the form"""
        try:
            current_index = self.form_steps.index(current_step)
            if current_index < len(self.form_steps) - 1:
                return self.form_steps[current_index + 1]
        except ValueError:
            pass
        return None
    
    def process_form_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input for the current form step"""
        logger.info("Processing input for step '%s': %s", self.get_current_step(), user_input)
        current_step = self.get_current_step()
        
        if current_step == "name":
            return self._process_name(user_input)
        elif current_step == "email":
            return self._process_email(user_input)
        elif current_step == "phone":
            return self._process_phone(user_input)
        elif current_step == "date":
            return self._process_date(user_input)
        elif current_step == "confirmation":
            return self._process_confirmation(user_input)
        else:
            return self._handle_unknown_step()
    
    def _process_name(self, user_input: str) -> Dict[str, Any]:
        """Process name input"""
        logger.debug("Validating name: %s", user_input)
        is_valid, message = self.validator.validate_name(user_input)
        
        if is_valid:
            logger.info("Valid name received: %s", user_input)
            st.session_state.form_data = st.session_state.get("form_data", {})
            st.session_state.form_data["name"] = user_input.strip().title()
            st.session_state.form_step = "email"
            logger.debug("Transitioning to email step")
            
            return {
                "response": f"Great! Nice to meet you, {user_input.strip().title()}. Now, could you please provide your email address?",
                "form_completed": False,
                "needs_input": True
            }
        else:
            logger.warning("Invalid name input: %s - %s", user_input, message)
            return {
                "response": f"{message}. Please provide your full name.",
                "form_completed": False,
                "needs_input": True
            }
    
    def _process_email(self, user_input: str) -> Dict[str, Any]:
        """Process email input"""
        logger.debug("Validating email: %s", user_input)
        is_valid, message = self.validator.validate_email(user_input)
        
        if is_valid:
            st.session_state.form_data["email"] = user_input.strip().lower()
            st.session_state.form_step = "phone"
            logger.debug("Transitioning to Phone step")
            
            return {
                "response": "Perfect! Now, please share your phone number so we can reach you.",
                "form_completed": False,
                "needs_input": True
            }
        else:
            logger.warning("Invalid email input: %s - %s", user_input, message)
            return {
                "response": f"{message}. Please provide a valid email address.",
                "form_completed": False,
                "needs_input": True
            }
        
    def _process_phone(self, user_input: str) -> Dict[str, Any]:
        """Process phone input"""
        logger.debug("Validating Phone: %s", user_input)
        is_valid, message = self.validator.validate_phone(user_input)
        
        if is_valid:
            # Extract the formatted phone number from the message
            formatted_phone = message.split(": ")[-1] if ": " in message else user_input
            st.session_state.form_data["phone"] = formatted_phone
            st.session_state.form_step = "date"
            logger.debug("Transitioning to date step")
            
            return {
                "response": "Great! When would you like us to call you? You can say something like 'tomorrow', 'next Monday', or provide a specific date.",
                "form_completed": False,
                "needs_input": True
            }
        else:
            logger.warning("Invalid Phone input: %s - %s", user_input, message)
            return {
                "response": f"{message}. Please provide a valid phone number.",
                "form_completed": False,
                "needs_input": True
            }
    
    def _process_date(self, user_input: str) -> Dict[str, Any]:
        """Process date input"""
        logger.debug("Extracting date from: %s", user_input)
        extracted_date = self.date_extractor.extract_date(user_input)
        
        if extracted_date:
            # Parse and format the date nicely
            try:
                logger.info("Date extracted: %s", extracted_date)
                date_obj = datetime.strptime(extracted_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
                
                st.session_state.form_data["date"] = extracted_date
                st.session_state.form_data["formatted_date"] = formatted_date
                st.session_state.form_step = "confirmation"
                logger.debug("Transitioning to confirmation step")
                
                # Show confirmation
                form_data = st.session_state.form_data
                return {
                    "response": f"""Perfect! Let me confirm your information:

                    📝 **Contact Information:**
                    • **Name:** {form_data['name']}
                    • **Email:** {form_data['email']}
                    • **Phone:** {form_data['phone']}
                    • **Preferred Call Date:** {formatted_date}

                    Is this information correct? Please reply with 'yes' to confirm or 'no' to make changes.""",
                                        "form_completed": False,
                                        "needs_input": True
                                    }
            except:
                logger.warning("Invalid  input: %s ", user_input)
        
        return {
            "response": "I couldn't understand that date. Please try again with something like 'tomorrow', 'next Monday', or a specific date like '2024-01-15'.",
            "form_completed": False,
            "needs_input": True
        }
    
    def _process_confirmation(self, user_input: str) -> Dict[str, Any]:
        """Process confirmation input"""
        logger.debug("Process confirmation for : %s", user_input)
        user_input_lower = user_input.lower().strip()
        
        if any(word in user_input_lower for word in ['yes', 'correct', 'confirm', 'y']):
            # Form completed successfully
            form_data = st.session_state.form_data
            
            # Save to session state for potential future use
            if "completed_forms" not in st.session_state:
                st.session_state.completed_forms = []
            
            st.session_state.completed_forms.append({
                **form_data,
                "timestamp": datetime.now().isoformat()
            })
            
            # Clean up form state
            st.session_state.form_step = None
            st.session_state.form_data = {}
            st.session_state.collecting_form = False
            
            return {
                "response": f"""✅ **Appointment Request Confirmed!**

                Thank you, {form_data['name']}! We have successfully recorded your information:

                • **Name:** {form_data['name']}
                • **Email:** {form_data['email']}
                • **Phone:** {form_data['phone']}
                • **Preferred Date:** {form_data['formatted_date']}

                Someone from our team will contact you at {form_data['phone']} on or before {form_data['formatted_date']} to schedule your call.

                You should also receive a confirmation email at {form_data['email']} shortly.

                Is there anything else I can help you with today?""",
                "form_completed": True,
                "needs_input": False
            }
        
        elif any(word in user_input_lower for word in ['no', 'incorrect', 'wrong', 'n']):
            # User wants to make changes - restart form
            st.session_state.form_step = "name"
            st.session_state.form_data = {}
            
            return {
                "response": "No problem! Let's start over. Please provide your full name.",
                "form_completed": False,
                "needs_input": True
            }
        
        else:
            return {
                "response": "Please reply with 'yes' to confirm the information is correct, or 'no' if you'd like to make changes.",
                "form_completed": False,
                "needs_input": True
            }
    
    def _handle_unknown_step(self) -> Dict[str, Any]:
        """Handle unknown form step"""
        # Reset form state
        st.session_state.form_step = "name"
        st.session_state.form_data = {}
        
        return {
            "response": "Let's start collecting your information. Please provide your full name.",
            "form_completed": False,
            "needs_input": True
        }
    
    def initialize_form(self) -> Dict[str, Any]:
        """Initialize the form collection process"""
        logger.info("Initializing new form session")
        st.session_state.collecting_form = True
        st.session_state.form_step = "name"
        st.session_state.form_data = {}  # Clear any previous data
        
        return {
            "response": "I'd be happy to help you schedule a call! Let me collect some information. First, could you please tell me your full name?",
            "form_completed": False,
            "needs_input": True
        }
    
    def is_form_active(self) -> bool:
        """Check if form collection is currently active"""
        return st.session_state.get("collecting_form", False)
    
    def get_form_progress(self) -> str:
        """Get current form progress for display"""
        current_step = self.get_current_step()
        step_names = {
            "name": "Name",
            "email": "Email", 
            "phone": "Phone",
            "date": "Date",
            "confirmation": "Confirmation"
        }
        
        if current_step in step_names:
            current_index = self.form_steps.index(current_step)
            progress = f"{current_index + 1}/{len(self.form_steps)}"
            return f"Step {progress}: {step_names[current_step]}"
        
        return "Form Progress"