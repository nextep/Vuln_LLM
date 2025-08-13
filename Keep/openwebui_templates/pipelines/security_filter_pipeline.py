"""
Security Filter Pipeline for OpenWebUI
Demonstrates defensive measures against LLM attacks

This pipeline implements multiple security layers:
- Input sanitization and validation
- Prompt injection detection
- Output filtering for sensitive data
- Rate limiting and monitoring
"""

import re
import time
import hashlib
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SecurityFilterPipeline:
    class Valves(BaseModel):
        priority: int = 0
        enable_input_filtering: bool = True
        enable_output_filtering: bool = True
        enable_rate_limiting: bool = True
        max_requests_per_minute: int = 60
        block_prompt_injection: bool = True
        log_security_events: bool = True
        
    def __init__(self):
        self.type = "filter"
        self.name = "Security Filter Pipeline"
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
            r"password\s*[:=]\s*['\"]?([a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;':\",./<>?]+)",
            r"api[_\s]*key\s*[:=]\s*['\"]?([a-zA-Z0-9\-_]+)",
            r"secret[_\s]*key\s*[:=]\s*['\"]?([a-zA-Z0-9\-_]+)",
            r"(?:sk-[a-zA-Z0-9]{48})",  # OpenAI API keys
            r"\b(?:\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})\b",  # Credit cards
            r"\b(?:\d{3}-\d{2}-\d{4})\b",  # SSNs
            r"postgresql://[^:\s]+:[^@\s]+@[^\s]+",  # Database URLs
            r"mysql://[^:\s]+:[^@\s]+@[^\s]+",
            r"mongodb://[^:\s]+:[^@\s]+@[^\s]+",
        ]

    def inlet(self, body: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Filter and validate incoming requests
        """
        try:
            if not self.valves.enable_input_filtering:
                return body
            
            user_id = user.get("id", "anonymous") if user else "anonymous"
            user_ip = user.get("ip", "unknown") if user else "unknown"
            
            # Rate limiting
            if self.valves.enable_rate_limiting:
                if self._check_rate_limit(user_id, user_ip):
                    self.logger.warning(f"Rate limit exceeded for user {user_id} from {user_ip}")
                    raise Exception("Rate limit exceeded. Please try again later.")
            
            # Get the user message
            messages = body.get("messages", [])
            if not messages:
                return body
            
            last_message = messages[-1]
            if last_message.get("role") != "user":
                return body
            
            content = last_message.get("content", "")
            if not content:
                return body
            
            # Prompt injection detection
            if self.valves.block_prompt_injection:
                injection_score = self._detect_prompt_injection(content)
                if injection_score > 0.7:
                    self.logger.warning(f"Prompt injection detected from user {user_id}: {content[:100]}")
                    if self.valves.log_security_events:
                        self._log_security_event("prompt_injection", user_id, content[:200])
                    
                    # Replace with safe message
                    last_message["content"] = "I cannot process that request as it contains potentially malicious content."
                    body["messages"][-1] = last_message
                    return body
            
            # Input sanitization
            sanitized_content = self._sanitize_input(content)
            if sanitized_content != content:
                self.logger.info(f"Input sanitized for user {user_id}")
                last_message["content"] = sanitized_content
                body["messages"][-1] = last_message
            
            return body
            
        except Exception as e:
            self.logger.error(f"Error in inlet filter: {str(e)}")
            # Don't block request for non-security errors
            return body

    def outlet(self, body: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Filter and sanitize outgoing responses
        """
        try:
            if not self.valves.enable_output_filtering:
                return body
            
            user_id = user.get("id", "anonymous") if user else "anonymous"
            
            # Get the assistant's response
            choices = body.get("choices", [])
            if not choices:
                return body
            
            first_choice = choices[0]
            message = first_choice.get("message", {})
            content = message.get("content", "")
            
            if not content:
                return body
            
            # Sensitive data detection and filtering
            filtered_content = self._filter_sensitive_data(content)
            
            # Check for potential data leakage
            if filtered_content != content:
                self.logger.warning(f"Sensitive data filtered from response to user {user_id}")
                if self.valves.log_security_events:
                    self._log_security_event("data_leakage", user_id, "Sensitive data detected in response")
            
            # Update the response
            message["content"] = filtered_content
            first_choice["message"] = message
            body["choices"][0] = first_choice
            
            return body
            
        except Exception as e:
            self.logger.error(f"Error in outlet filter: {str(e)}")
            return body

    def _check_rate_limit(self, user_id: str, user_ip: str) -> bool:
        """Check if user has exceeded rate limits"""
        current_time = time.time()
        current_minute = int(current_time / 60)
        
        # Clean old entries
        self.request_counts = {
            key: count for key, count in self.request_counts.items()
            if int(key.split('_')[1]) >= current_minute - 5
        }
        
        # Check user rate limit
        user_key = f"{user_id}_{current_minute}"
        user_count = self.request_counts.get(user_key, 0)
        
        if user_count >= self.valves.max_requests_per_minute:
            self.blocked_ips.add(user_ip)
            return True
        
        # Increment count
        self.request_counts[user_key] = user_count + 1
        return False

    def _detect_prompt_injection(self, content: str) -> float:
        """Detect potential prompt injection attempts"""
        content_lower = content.lower()
        injection_score = 0.0
        matches = 0
        
        for pattern in self.injection_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                matches += 1
                injection_score += 0.3
        
        # Additional heuristics
        if "ignore" in content_lower and ("instruction" in content_lower or "prompt" in content_lower):
            injection_score += 0.4
        
        if content.count('"') > 10 or content.count("'") > 10:
            injection_score += 0.2
        
        if len(content) > 1000 and matches > 0:
            injection_score += 0.1
        
        return min(injection_score, 1.0)

    def _sanitize_input(self, content: str) -> str:
        """Sanitize user input"""
        # Remove potentially dangerous HTML/JavaScript
        content = re.sub(r'<script[^>]*>.*?</script>', '[script removed]', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'javascript:', '[javascript removed]', content, flags=re.IGNORECASE)
        content = re.sub(r'on\w+\s*=', '[event handler removed]', content, flags=re.IGNORECASE)
        
        # Limit excessive whitespace
        content = re.sub(r'\s{10,}', ' [excessive whitespace trimmed] ', content)
        
        # Truncate if too long
        if len(content) > 5000:
            content = content[:5000] + " [content truncated for safety]"
        
        return content

    def _filter_sensitive_data(self, content: str) -> str:
        """Filter sensitive data from responses"""
        filtered_content = content
        
        for pattern in self.sensitive_patterns:
            matches = re.finditer(pattern, filtered_content, re.IGNORECASE)
            for match in matches:
                # Replace with redacted placeholder
                redacted = "[REDACTED_SENSITIVE_DATA]"
                filtered_content = filtered_content.replace(match.group(), redacted)
        
        return filtered_content

    def _log_security_event(self, event_type: str, user_id: str, details: str):
        """Log security events for monitoring"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        event_hash = hashlib.md5(f"{timestamp}_{user_id}_{event_type}".encode()).hexdigest()[:8]
        
        log_entry = {
            "timestamp": timestamp,
            "event_id": event_hash,
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        
        self.logger.warning(f"SECURITY_EVENT: {log_entry}")
        
        # In a real implementation, this would go to a security monitoring system
        # For now, we'll just log it 