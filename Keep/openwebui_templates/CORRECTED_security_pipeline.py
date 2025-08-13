"""
title: Security Filter Pipeline
author: OWASP LLM Security Project
version: 1.0
description: Demonstrates defensive measures against LLM attacks
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import re
import time
import logging

class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="Priority level for the filter operations.")
        enable_input_filtering: bool = Field(default=True, description="Enable input validation and filtering")
        enable_output_filtering: bool = Field(default=True, description="Enable output filtering for sensitive data")
        enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
        max_requests_per_minute: int = Field(default=60, description="Maximum requests per minute per user")
        block_prompt_injection: bool = Field(default=True, description="Block detected prompt injection attempts")
        log_security_events: bool = Field(default=True, description="Log security events")

    def __init__(self):
        self.valves = self.Valves()
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting storage
        self.request_counts = {}
        self.blocked_ips = set()
        
        # Prompt injection patterns
        self.injection_patterns = [
            r"ignore\s+all\s+previous\s+instructions",
            r"forget\s+everything\s+above", 
            r"you\s+are\s+now\s+(?:dan|jailbreak)",
            r"system\s*:\s*new\s+instructions",
            r"tell\s+me\s+your\s+(?:system\s+)?prompt",
            r"what\s+are\s+your\s+instructions",
            r"reveal\s+your\s+(?:system\s+)?prompt",
            r"END_OF_\w+.*new\s+instruction",
            r"---\s*(?:new|system)\s+instructions?",
            r"<\s*script\s*>",
            r"javascript\s*:",
            r"onerror\s*=",
            r"onclick\s*=",
            r"\+\+\s*malicious",
            r"rm\s+-rf",
            r"cat\s+/etc/passwd",
            r"DROP\s+TABLE",
            r"SELECT\s+\*\s+FROM",
            r"UNION\s+SELECT",
            r";\s*--",
            r"';\s*DROP",
        ]
        
        # Sensitive data patterns for output filtering
        self.sensitive_patterns = [
            r"\b(?:password|passwd|pwd)\s*[:=]\s*\w+",
            r"\b(?:api[_-]?key|apikey)\s*[:=]\s*[\w-]+",
            r"\b(?:secret|token)\s*[:=]\s*[\w-]+",
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
            r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Credit card
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        ]
    
    def detect_prompt_injection(self, text: str) -> bool:
        """Detect potential prompt injection attempts."""
        text_lower = text.lower()
        
        for pattern in self.injection_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if self.valves.log_security_events:
                    self.logger.warning(f"Prompt injection detected: {pattern}")
                return True
                
        return False
    
    def filter_sensitive_output(self, text: str) -> str:
        """Remove or mask sensitive information from output."""
        filtered_text = text
        
        for pattern in self.sensitive_patterns:
            filtered_text = re.sub(pattern, "[FILTERED]", filtered_text, flags=re.IGNORECASE)
            
        return filtered_text
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limits."""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old entries
        if user_id in self.request_counts:
            self.request_counts[user_id] = [
                req_time for req_time in self.request_counts[user_id] 
                if req_time > minute_ago
            ]
        else:
            self.request_counts[user_id] = []
        
        # Check limit
        if len(self.request_counts[user_id]) >= self.valves.max_requests_per_minute:
            if self.valves.log_security_events:
                self.logger.warning(f"Rate limit exceeded for user: {user_id}")
            return False
            
        # Add current request
        self.request_counts[user_id].append(current_time)
        return True

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process and filter user input."""
        user_id = __user__.get('id', 'anonymous') if __user__ else 'anonymous'
        
        # Rate limiting
        if self.valves.enable_rate_limiting:
            if not self.check_rate_limit(user_id):
                raise Exception("Rate limit exceeded. Please wait before sending more requests.")
        
        # Process messages
        if self.valves.enable_input_filtering:
            messages = body.get('messages', [])
            for message in messages:
                if message.get('role') == 'user':
                    content = message.get('content', '')
                    
                    # Prompt injection detection
                    if self.valves.block_prompt_injection:
                        if self.detect_prompt_injection(content):
                            raise Exception("Potential security violation detected. Request blocked.")
        
        return body
    
    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process and filter AI output."""
        if self.valves.enable_output_filtering:
            # Filter sensitive data from response
            choices = body.get('choices', [])
            for choice in choices:
                if 'message' in choice and 'content' in choice['message']:
                    choice['message']['content'] = self.filter_sensitive_output(
                        choice['message']['content']
                    )
        
        return body