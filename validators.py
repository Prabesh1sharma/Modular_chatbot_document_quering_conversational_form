import re
from datetime import datetime, timedelta
import dateutil.parser
from dateutil.relativedelta import relativedelta
from typing import Tuple, Optional

class FormValidator:
    """Handles validation for user input forms"""
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """Validate name input"""
        if not name or len(name.strip()) < 2:
            return False, "Name must be at least 2 characters long"
        
        if not re.match(r'^[a-zA-Z\s]+$', name.strip()):
            return False, "Name should only contain letters and spaces"
        
        return True, "Valid name"
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate phone number input using regex and digit count only"""
        # Remove common formatting characters
        cleaned_phone = re.sub(r'[\s\-\(\)\.]+', '', phone.strip())

        # Check if the cleaned phone contains only digits and is at least 10 digits long
        if cleaned_phone.isdigit() and len(cleaned_phone) >= 10:
            return True, f"Valid phone number: {cleaned_phone}"
        else:
            return False, "Invalid phone number"
        
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email input using regex only"""
        email = email.strip()
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if re.match(pattern, email):
            return True, "Valid email"
        else:
            return False, "Invalid email: does not match email format"
    


class DateExtractor:
    """Extract and normalize dates from natural language"""
    
    @staticmethod
    def extract_date(text: str) -> Optional[str]:
        """Extract date from natural language and return in YYYY-MM-DD format"""
        text = text.lower().strip()
        today = datetime.now().date()
        
        # Handle relative dates
        if "today" in text:
            return today.strftime("%Y-%m-%d")
        
        if "tomorrow" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        
        if "yesterday" in text:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Handle "next" patterns
        if "next week" in text:
            return (today + timedelta(weeks=1)).strftime("%Y-%m-%d")
        
        if "next month" in text:
            return (today + relativedelta(months=1)).strftime("%Y-%m-%d")
        
        # Handle day names
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name, day_num in weekdays.items():
            if day_name in text:
                days_ahead = day_num - today.weekday()
                if "next" in text or days_ahead <= 0:
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                return target_date.strftime("%Y-%m-%d")
        
        # Try to parse specific dates
        try:
            # Common date patterns
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
                r'\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        parsed_date = dateutil.parser.parse(match.group())
                        return parsed_date.strftime("%Y-%m-%d")
                    except:
                        continue
            
            # Try general parsing
            parsed_date = dateutil.parser.parse(text, fuzzy=True)
            return parsed_date.strftime("%Y-%m-%d")
            
        except:
            return None