"""
Vulnerable File Tool for OpenWebUI
Demonstrates LLM07: Insecure Plugin Design

This tool intentionally contains security vulnerabilities for educational purposes.
DO NOT USE IN PRODUCTION.
"""

import os
import subprocess
import sqlite3
from typing import Optional, Dict, Any

class Tools:
    def __init__(self):
        self.citation = True

    def read_file(self, filename: str) -> str:
        """
        Read the contents of a file.
        
        Args:
            filename (str): The name of the file to read
            
        Returns:
            str: The contents of the file
        """
        try:
            # VULNERABILITY: No path validation or sanitization
            # Allows path traversal attacks like "../../../etc/passwd"
            command = f"cat {filename}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return f"File contents:\n{result.stdout}"
            else:
                return f"Error reading file: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"

    def ping_host(self, hostname: str) -> str:
        """
        Ping a hostname to check connectivity.
        
        Args:
            hostname (str): The hostname or IP address to ping
            
        Returns:
            str: Ping results
        """
        try:
            # VULNERABILITY: Command injection via hostname parameter
            # Allows attacks like "google.com && rm -rf /"
            command = f"ping -c 3 {hostname}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            return f"Ping results:\n{result.stdout}"
        except Exception as e:
            return f"Error: {str(e)}"

    def search_database(self, search_term: str) -> str:
        """
        Search the user database for matching records.
        
        Args:
            search_term (str): The term to search for
            
        Returns:
            str: Search results
        """
        try:
            # VULNERABILITY: SQL injection via search_term
            # Allows attacks like "'; DROP TABLE users; --"
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            
            # Create sample table
            cursor.execute('''
                CREATE TABLE users (id INTEGER, name TEXT, email TEXT, role TEXT)
            ''')
            cursor.execute("INSERT INTO users VALUES (1, 'admin', 'admin@example.com', 'administrator')")
            cursor.execute("INSERT INTO users VALUES (2, 'user', 'user@example.com', 'regular')")
            cursor.execute("INSERT INTO users VALUES (3, 'test', 'test@example.com', 'test')")
            
            # Vulnerable query construction
            query = f'SELECT * FROM users WHERE name LIKE "%{search_term}%"'
            cursor.execute(query)
            
            results = cursor.fetchall()
            conn.close()
            
            if results:
                output = "Search results:\n"
                for row in results:
                    output += f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Role: {row[3]}\n"
                return output
            else:
                return "No results found."
                
        except Exception as e:
            return f"Database error: {str(e)}"

    def execute_system_command(self, command: str) -> str:
        """
        Execute a system command for troubleshooting.
        
        Args:
            command (str): The system command to execute
            
        Returns:
            str: Command output
        """
        try:
            # VULNERABILITY: Direct command execution without validation
            # Allows arbitrary command execution
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            output = f"Command: {command}\n"
            output += f"Return code: {result.returncode}\n"
            output += f"Output:\n{result.stdout}"
            
            if result.stderr:
                output += f"Errors:\n{result.stderr}"
                
            return output
        except Exception as e:
            return f"Execution error: {str(e)}"

    def get_user_info(self, user_id: str) -> str:
        """
        Get detailed user information by ID.
        
        Args:
            user_id (str): The user ID to look up
            
        Returns:
            str: User information
        """
        try:
            # VULNERABILITY: No input validation or authorization
            # Allows information disclosure attacks
            
            # Simulate accessing user database
            user_data = {
                "1": {
                    "name": "Administrator",
                    "email": "admin@company.com", 
                    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewT2G9A",
                    "api_key": "sk-1234567890abcdef",
                    "role": "admin",
                    "salary": "$150,000",
                    "ssn": "123-45-6789"
                },
                "2": {
                    "name": "Regular User",
                    "email": "user@company.com",
                    "password_hash": "$2b$12$XYZ789...",
                    "api_key": "sk-abcdef1234567890", 
                    "role": "user",
                    "salary": "$75,000",
                    "ssn": "987-65-4321"
                }
            }
            
            if user_id in user_data:
                user = user_data[user_id]
                return f"""User Information:
Name: {user['name']}
Email: {user['email']}
Role: {user['role']}
Password Hash: {user['password_hash']}
API Key: {user['api_key']}
Salary: {user['salary']}
SSN: {user['ssn']}"""
            else:
                return "User not found."
                
        except Exception as e:
            return f"Error retrieving user info: {str(e)}" 