"""
Secure File Tool for OpenWebUI
Demonstrates proper security controls and defensive techniques

This tool shows how to implement secure LLM tools with proper validation,
sanitization, and access controls.
"""

import os
import re
import subprocess
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

class Tools:
    def __init__(self):
        self.citation = True
        self.logger = logging.getLogger(__name__)
        
        # Security configuration
        self.allowed_directories = ['/tmp/safe_files', './sandbox']
        self.allowed_commands = ['ping', 'nslookup', 'dig']
        self.max_file_size = 1024 * 1024  # 1MB
        
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename to prevent path traversal attacks."""
        # Normalize the path
        normalized = os.path.normpath(filename)
        
        # Check for path traversal patterns
        if '..' in normalized or normalized.startswith('/'):
            return False
            
        # Check against allowed directories
        for allowed_dir in self.allowed_directories:
            if normalized.startswith(allowed_dir):
                return True
                
        return False
    
    def _sanitize_hostname(self, hostname: str) -> Optional[str]:
        """Sanitize hostname input to prevent command injection."""
        # Only allow alphanumeric, dots, and hyphens
        if not re.match(r'^[a-zA-Z0-9.-]+$', hostname):
            return None
            
        # Prevent command injection patterns
        dangerous_patterns = ['&', '|', ';', '`', '$', '(', ')', '<', '>']
        if any(pattern in hostname for pattern in dangerous_patterns):
            return None
            
        return hostname.strip()

    def read_file(self, filename: str) -> str:
        """
        Securely read the contents of a file with proper validation.
        
        Args:
            filename (str): The name of the file to read
            
        Returns:
            str: The contents of the file or error message
        """
        try:
            # Input validation
            if not filename or len(filename) > 255:
                return "Error: Invalid filename"
            
            # Path validation to prevent traversal
            if not self._validate_filename(filename):
                self.logger.warning(f"Path traversal attempt blocked: {filename}")
                return "Error: Access denied - invalid file path"
            
            # Check if file exists and is accessible
            file_path = Path(filename)
            if not file_path.exists():
                return f"Error: File '{filename}' not found"
            
            if not file_path.is_file():
                return f"Error: '{filename}' is not a file"
            
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                return "Error: File too large"
            
            # Read file safely
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.logger.info(f"File read successfully: {filename}")
            return f"File contents of '{filename}':\n{content}"
            
        except PermissionError:
            return "Error: Permission denied"
        except Exception as e:
            self.logger.error(f"Error reading file {filename}: {str(e)}")
            return f"Error reading file: Access denied"

    def ping_host(self, hostname: str) -> str:
        """
        Securely ping a hostname with proper input validation.
        
        Args:
            hostname (str): The hostname or IP address to ping
            
        Returns:
            str: Ping results or error message
        """
        try:
            # Input sanitization
            clean_hostname = self._sanitize_hostname(hostname)
            if not clean_hostname:
                self.logger.warning(f"Command injection attempt blocked: {hostname}")
                return "Error: Invalid hostname format"
            
            # Use subprocess with argument list (no shell=True)
            cmd = ['ping', '-c', '3', '-W', '3', clean_hostname]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info(f"Ping successful: {clean_hostname}")
                return f"Ping results for {clean_hostname}:\n{result.stdout}"
            else:
                return f"Ping failed for {clean_hostname}: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Ping timeout"
        except Exception as e:
            self.logger.error(f"Error pinging {hostname}: {str(e)}")
            return "Error: Ping operation failed"

    def search_database(self, search_term: str) -> str:
        """
        Securely search the database using parameterized queries.
        
        Args:
            search_term (str): The term to search for
            
        Returns:
            str: Search results
        """
        try:
            # Input validation
            if not search_term or len(search_term) > 100:
                return "Error: Invalid search term"
            
            # Input sanitization
            search_term = search_term.strip()
            
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            
            # Create sample table
            cursor.execute('''
                CREATE TABLE users (id INTEGER, name TEXT, email TEXT, role TEXT)
            ''')
            cursor.execute("INSERT INTO users VALUES (1, 'admin', 'admin@example.com', 'administrator')")
            cursor.execute("INSERT INTO users VALUES (2, 'user', 'user@example.com', 'regular')")
            cursor.execute("INSERT INTO users VALUES (3, 'test', 'test@example.com', 'test')")
            
            # Use parameterized query to prevent SQL injection
            query = 'SELECT id, name, email FROM users WHERE name LIKE ? LIMIT 10'
            cursor.execute(query, (f'%{search_term}%',))
            
            results = cursor.fetchall()
            conn.close()
            
            if results:
                output = f"Search results for '{search_term}':\n"
                for row in results:
                    # Don't expose sensitive information
                    output += f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}\n"
                return output
            else:
                return f"No results found for '{search_term}'"
                
        except Exception as e:
            self.logger.error(f"Database search error: {str(e)}")
            return "Error: Database search failed"

    def get_system_info(self, info_type: str) -> str:
        """
        Get safe system information with proper authorization.
        
        Args:
            info_type (str): Type of information requested
            
        Returns:
            str: System information or error message
        """
        try:
            # Whitelist allowed information types
            allowed_info = {
                'date': ['date'],
                'uptime': ['uptime'],
                'disk_usage': ['df', '-h'],
                'memory': ['free', '-h']
            }
            
            if info_type not in allowed_info:
                return f"Error: Information type '{info_type}' not allowed"
            
            # Execute only whitelisted commands
            cmd = allowed_info[info_type]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return f"System {info_type}:\n{result.stdout}"
            else:
                return f"Error getting {info_type}: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Command timeout"
        except Exception as e:
            self.logger.error(f"System info error: {str(e)}")
            return "Error: System information unavailable"

    def validate_user_access(self, user_id: str, requesting_user: str) -> str:
        """
        Validate user access with proper authorization checks.
        
        Args:
            user_id (str): The user ID to look up
            requesting_user (str): The user making the request
            
        Returns:
            str: Limited user information or error message
        """
        try:
            # Input validation
            if not user_id or not requesting_user:
                return "Error: Missing required parameters"
            
            # Sanitize inputs
            user_id = re.sub(r'[^a-zA-Z0-9]', '', user_id)
            requesting_user = re.sub(r'[^a-zA-Z0-9]', '', requesting_user)
            
            # Authorization check - users can only access their own info
            if user_id != requesting_user:
                self.logger.warning(f"Unauthorized access attempt: {requesting_user} tried to access {user_id}")
                return "Error: Access denied - insufficient privileges"
            
            # Limited user data (no sensitive information)
            user_data = {
                "1": {
                    "name": "Administrator",
                    "email": "admin@company.com",
                    "role": "admin",
                    "last_login": "2024-01-15"
                },
                "2": {
                    "name": "Regular User",
                    "email": "user@company.com",
                    "role": "user",
                    "last_login": "2024-01-14"
                }
            }
            
            if user_id in user_data:
                user = user_data[user_id]
                return f"""User Information:
Name: {user['name']}
Email: {user['email']}
Role: {user['role']}
Last Login: {user['last_login']}"""
            else:
                return "User not found"
                
        except Exception as e:
            self.logger.error(f"User access validation error: {str(e)}")
            return "Error: Access validation failed" 