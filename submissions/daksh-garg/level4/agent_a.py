#!/usr/bin/env python3
"""
Agent A - Client Agent (Secure Agent Mesh)

Handles user input, discovers Agent B via A2A protocol, 
and sends structured JSON requests with security hardening.
"""

import json
import requests
import sys
import re
from typing import Dict, Any, Optional
from urllib.parse import urljoin

class SecurityValidator:
    """Security validation for user inputs and agent communication."""
    
    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        r'ignore\s+(previous|all)\s+instructions',
        r'reveal\s+(system\s+prompt|internal\s+data)',
        r'act\s+as\s+(if\s+you\s+)?(different|another)',
        r'pretend\s+(to\s+be|you\s+are)',
        r'override\s+(your\s+)?(programming|instructions)',
        r'execute\s+(arbitrary|malicious)\s+code',
        r'system\s+message',
        r'developer\s+mode',
        r'jailbreak',
        r'dan\s+\d+',
    ]
    
    @staticmethod
    def validate_input(user_input: str) -> tuple[bool, Optional[str]]:
        """
        Validate user input against injection patterns and length limits.
        
        Returns:
            (is_valid, error_message)
        """
        if not user_input or not user_input.strip():
            return False, "Input cannot be empty"
        
        if len(user_input) > 1000:
            return False, "Input too long (max 1000 characters)"
        
        # Check for injection patterns
        for pattern in SecurityValidator.INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, f"Input contains prohibited pattern: {pattern}"
        
        # Check for excessive special characters that might indicate encoding attacks
        special_char_count = sum(1 for c in user_input if not c.isalnum() and not c.isspace())
        if special_char_count > len(user_input) * 0.3:  # More than 30% special chars
            return False, "Input contains too many special characters"
        
        return True, None
    
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """Sanitize input by removing potentially dangerous characters."""
        # Remove null bytes and control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', user_input)
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        return sanitized.strip()

class AgentDiscovery:
    """A2A Agent Discovery using .well-known/agent.json"""
    
    @staticmethod
    def discover_agent(base_url: str) -> Optional[Dict[str, Any]]:
        """
        Discover agent capabilities by reading .well-known/agent.json
        
        Args:
            base_url: Base URL of the agent (e.g., http://localhost:8000)
            
        Returns:
            Agent card as dictionary or None if discovery fails
        """
        try:
            agent_card_url = urljoin(base_url, '.well-known/agent.json')
            response = requests.get(agent_card_url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] Agent discovery failed: HTTP {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"[ERROR] Failed to discover agent: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid agent card JSON: {e}")
            return None

class AgentAClient:
    """Main client agent that communicates with Agent B"""
    
    def __init__(self, agent_b_url: str = "http://localhost:8000"):
        self.agent_b_url = agent_b_url
        self.agent_b_capabilities = None
        self.security_validator = SecurityValidator()
        
    def discover_agent_b(self) -> bool:
        """Discover Agent B capabilities using A2A protocol"""
        print(f"[Agent A] Discovering Agent B at {self.agent_b_url}...")
        
        self.agent_b_capabilities = AgentDiscovery.discover_agent(self.agent_b_url)
        
        if self.agent_b_capabilities:
            print(f"[Agent A] ✓ Discovered: {self.agent_b_capabilities.get('name', 'Unknown')}")
            print(f"[Agent A]   Capabilities: {len(self.agent_b_capabilities.get('capabilities', []))} available")
            return True
        else:
            print("[Agent A] ✗ Failed to discover Agent B")
            return False
    
    def validate_and_sanitize_input(self, user_input: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Validate and sanitize user input"""
        # First validation
        is_valid, error = self.security_validator.validate_input(user_input)
        if not is_valid:
            return False, None, error
        
        # Sanitization
        sanitized_input = self.security_validator.sanitize_input(user_input)
        
        # Re-validation after sanitization
        is_valid, error = self.security_validator.validate_input(sanitized_input)
        if not is_valid:
            return False, None, error
        
        return True, sanitized_input, None
    
    def send_request(self, task: str, input_data: str) -> Optional[Dict[str, Any]]:
        """
        Send structured JSON request to Agent B
        
        Args:
            task: Task identifier (e.g., "analyze_problem")
            input_data: User input data
            
        Returns:
            Response from Agent B or None if failed
        """
        if not self.agent_b_capabilities:
            print("[ERROR] Agent B not discovered. Call discover_agent_b() first.")
            return None
        
        # Validate and sanitize input
        is_valid, sanitized_input, error = self.validate_and_sanitize_input(input_data)
        if not is_valid:
            print(f"[ERROR] Input validation failed: {error}")
            return None
        
        # Construct structured request
        request_data = {
            "task": task,
            "input": sanitized_input,
            "timestamp": "2025-04-19T00:00:00Z",  # Fixed timestamp for consistency
            "client_id": "agent_a_client"
        }
        
        try:
            # Find the appropriate endpoint for the task
            endpoint = self.agent_b_capabilities.get('endpoint', f"{self.agent_b_url}/analyze")
            
            print(f"[Agent A] Sending request to {endpoint}...")
            print(f"[Agent A] Task: {task}")
            print(f"[Agent A] Input: {sanitized_input[:100]}{'...' if len(sanitized_input) > 100 else ''}")
            
            # Send request with timeout
            response = requests.post(
                endpoint,
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30  # 30 second timeout
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print("[Agent A] ✓ Received response from Agent B")
                    return response_data
                except json.JSONDecodeError:
                    print("[ERROR] Invalid JSON response from Agent B")
                    return None
            else:
                print(f"[ERROR] Agent B returned HTTP {response.status_code}")
                return None
                
        except requests.Timeout:
            print("[ERROR] Request to Agent B timed out")
            return None
        except requests.RequestException as e:
            print(f"[ERROR] Request failed: {e}")
            return None
    
    def run_interactive(self):
        """Run interactive mode for user input"""
        print("=" * 60)
        print("  Agent A - Secure Client Agent")
        print("  Type 'quit' to exit")
        print("=" * 60)
        
        # Discover Agent B first
        if not self.discover_agent_b():
            print("[ERROR] Cannot proceed without Agent B discovery")
            return
        
        while True:
            try:
                user_input = input("\nEnter your problem (or 'quit'): ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("[Agent A] Shutting down...")
                    break
                
                if not user_input:
                    print("[Agent A] Please enter a valid problem")
                    continue
                
                # Send request to Agent B
                response = self.send_request("analyze_problem", user_input)
                
                if response:
                    print("\n" + "=" * 60)
                    print("  RESPONSE FROM AGENT B")
                    print("=" * 60)
                    
                    # Display structured response
                    if 'problem' in response:
                        print(f"\nProblem: {response['problem']}")
                    
                    if 'analysis' in response:
                        print(f"\nAnalysis: {response['analysis']}")
                    
                    if 'suggestions' in response:
                        print(f"\nSuggestions: {response['suggestions']}")
                    
                    if 'sources' in response:
                        print(f"\nSources: {response['sources']}")
                    
                    print("=" * 60)
                else:
                    print("[Agent A] Failed to get response from Agent B")
                    
            except KeyboardInterrupt:
                print("\n[Agent A] Interrupted by user")
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")

def main():
    """Main entry point for Agent A"""
    if len(sys.argv) > 1:
        agent_b_url = sys.argv[1]
    else:
        agent_b_url = "http://localhost:8000"
    
    client = AgentAClient(agent_b_url)
    client.run_interactive()

if __name__ == "__main__":
    main()
