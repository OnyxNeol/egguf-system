"""
Agentic skills extension for EGGUF.

This module provides the EGGUF_AGENT class for agentic capabilities including
terminal interaction, cloud API access, and advanced reasoning.
"""

import json
import subprocess
import time
import requests
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from .core import ExtensionDef


class EGGUF_AGENT:
    """
    Agentic skills extension for EGGUF models.
    
    Provides terminal access, cloud API calls, file operations, and advanced
    reasoning capabilities for EGGUF-enabled AI systems.
    """
    
    def __init__(self, system_prompt: str = ""):
        """
        Initialize agent skill.
        
        Args:
            system_prompt: System prompt for agent behavior
        """
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.available_tools = self._get_available_tools()
        self.session_history = []
        self.cloud_sessions = {}
        self.is_initialized = False
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for agentic behavior."""
        return (
            "You are an autonomous AI agent with access to tools including terminal commands, "
            "file operations, and cloud APIs. You can execute complex multi-step tasks by "
            "combining these capabilities. Always prioritize safety and ask for clarification "
            "when instructions are ambiguous."
        )
    
    def _get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get available agentic tools."""
        return {
            "execute_command": {
                "description": "Execute a terminal/shell command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute"
                        },
                        "timeout": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 300,
                            "default": 30,
                            "description": "Timeout in seconds"
                        },
                        "capture_output": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to capture stdout/stderr"
                        }
                    },
                    "required": ["command"]
                },
                "gateway": "local"
            },
            "read_file": {
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file to read"
                        },
                        "encoding": {
                            "type": "string",
                            "default": "utf-8",
                            "description": "File encoding"
                        },
                        "max_lines": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Maximum lines to read (0 for all)"
                        }
                    },
                    "required": ["file_path"]
                },
                "gateway": "local"
            },
            "write_file": {
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to file"
                        },
                        "mode": {
                            "type": "string",
                            "default": "w",
                            "description": "File mode (w, a, x)"
                        },
                        "encoding": {
                            "type": "string",
            "default": "utf-8"
                        }
                    },
                    "required": ["file_path", "content"]
                },
                "gateway": "local"
            },
            "cloud_api": {
                "description": "Make HTTP requests to cloud APIs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "API endpoint URL"
                        },
                        "method": {
                            "type": "string",
                            "default": "GET",
                            "description": "HTTP method (GET, POST, PUT, DELETE, PATCH)"
                        },
                        "headers": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                            "description": "HTTP headers"
                        },
                        "data": {
                            "type": "object",
                            "description": "Request body data (for POST/PUT)"
                        },
                        "timeout": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 300,
                            "default": 30,
                            "description": "Request timeout in seconds"
                        },
                        "auth": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["bearer", "basic", "api_key"]
                                },
                                "token": {"type": "string"},
                                "username": {"type": "string"},
                                "password": {"type": "string"}
                            }
                        }
                    },
                    "required": ["url"]
                },
                "gateway": "cloud"
            },
            "reason": {
                "description": "Perform multi-step reasoning on a problem",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "problem": {
                            "type": "string",
                            "description": "Problem or question to solve"
                        },
                        "steps": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 20,
                            "default": 5,
                            "description": "Number of reasoning steps"
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context for reasoning"
                        }
                    },
                    "required": ["problem"]
                },
                "gateway": "local"
            },
            "plan": {
                "description": "Create a step-by-step execution plan",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "Goal or objective to achieve"
                        },
                        "constraints": {
                            "type": "string",
                            "description": "Constraints or limitations to consider"
                        },
                        "resources": {
                            "type": "string",
                            "description": "Available resources"
                        }
                    },
                    "required": ["goal"]
                },
                "gateway": "local"
            }
        }
    
    def initialize(self) -> bool:
        """
        Initialize the agent skill.
        
        Returns:
            bool: True if initialization successful
        """
        if self.is_initialized:
            return True
        
        try:
            self.session_history = []
            self.cloud_sessions = {}
            self.is_initialized = True
            print(f"✅ Initialized EGGUF Agent")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 30, capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute a terminal/shell command.
        
        Args:
            command: Shell command to execute
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dict containing execution results
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize agent")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            output_data = {
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "execution_time": execution_time,
                "success": result.returncode == 0,
                "timestamp": time.time()
            }
            
            # Add to session history
            self.session_history.append({
                "tool": "execute_command",
                "input": {"command": command, "timeout": timeout},
                "result": output_data,
                "timestamp": time.time()
            })
            
            print(f"💻 Executed command: {command}")
            return output_data
            
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "error": "Command timed out",
                "timeout": timeout,
                "execution_time": timeout,
                "success": False,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "command": command,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "success": False,
                "timestamp": time.time()
            }
    
    def read_file(self, file_path: str, encoding: str = "utf-8", max_lines: int = 0) -> Dict[str, Any]:
        """
        Read contents of a file.
        
        Args:
            file_path: Path to file to read
            encoding: File encoding
            max_lines: Maximum lines to read (0 for all)
            
        Returns:
            Dict containing file contents
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize agent")
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "file_path": file_path,
                    "error": "File not found",
                    "success": False,
                    "timestamp": time.time()
                }
            
            with open(path, 'r', encoding=encoding) as f:
                if max_lines > 0:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line)
                    content = ''.join(lines)
                else:
                    content = f.read()
            
            result = {
                "file_path": file_path,
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1 if content else 0,
                "encoding": encoding,
                "success": True,
                "timestamp": time.time()
            }
            
            self.session_history.append({
                "tool": "read_file",
                "input": {"file_path": file_path, "encoding": encoding, "max_lines": max_lines},
                "result": result,
                "timestamp": time.time()
            })
            
            print(f"📖 Read file: {file_path}")
            return result
            
        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e),
                "success": False,
                "timestamp": time.time()
            }
    
    def write_file(self, file_path: str, content: str, mode: str = "w", encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            file_path: Path to file to write
            content: Content to write to file
            mode: File mode (w, a, x)
            encoding: File encoding
            
        Returns:
            Dict containing write results
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize agent")
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            result = {
                "file_path": file_path,
                "bytes_written": len(content.encode(encoding)),
                "mode": mode,
                "encoding": encoding,
                "success": True,
                "timestamp": time.time()
            }
            
            self.session_history.append({
                "tool": "write_file",
                "input": {"file_path": file_path, "content": content, "mode": mode, "encoding": encoding},
                "result": result,
                "timestamp": time.time()
            })
            
            print(f"💾 Wrote file: {file_path}")
            return result
            
        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e),
                "success": False,
                "timestamp": time.time()
            }
    
    def cloud_api(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None,
                  data: Optional[Dict[str, Any]] = None, timeout: int = 30,
                  auth: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make HTTP requests to cloud APIs.
        
        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            headers: HTTP headers
            data: Request body data (for POST/PUT)
            timeout: Request timeout in seconds
            auth: Authentication configuration
            
        Returns:
            Dict containing API response
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize agent")
        
        start_time = time.time()
        
        try:
            # Prepare headers
            request_headers = headers or {}
            
            # Prepare authentication
            if auth:
                auth_type = auth.get("type", "").lower()
                if auth_type == "bearer":
                    token = auth.get("token")
                    if token:
                        request_headers["Authorization"] = f"Bearer {token}"
                elif auth_type == "basic":
                    username = auth.get("username")
                    password = auth.get("password")
                    if username and password:
                        import base64
                        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                        request_headers["Authorization"] = f"Basic {credentials}"
                elif auth_type == "api_key":
                    # For API key, typically passed as header or query param
                    key_name = auth.get("key_name", "X-API-Key")
                    key_value = auth.get("key_value")
                    if key_value:
                        request_headers[key_name] = key_value
            
            # Make request
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=request_headers,
                json=data if data else None,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            # Try to parse JSON response
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = response.text
            
            result = {
                "url": url,
                "method": method.upper(),
                "status_code": response.status_code,
                "response": response_data,
                "headers": dict(response.headers),
                "execution_time": execution_time,
                "success": 200 <= response.status_code < 300,
                "timestamp": time.time()
            }
            
            self.session_history.append({
                "tool": "cloud_api",
                "input": {
                    "url": url,
                    "method": method,
                    "headers": headers,
                    "data": data,
                    "timeout": timeout
                },
                "result": result,
                "timestamp": time.time()
            })
            
            print(f"☁️  Called cloud API: {method} {url}")
            return result
            
        except requests.exceptions.Timeout:
            return {
                "url": url,
                "method": method.upper(),
                "error": "Request timed out",
                "timeout": timeout,
                "execution_time": timeout,
                "success": False,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "url": url,
                "method": method.upper(),
                "error": str(e),
                "execution_time": time.time() - start_time,
                "success": False,
                "timestamp": time.time()
            }
    
    def reason(self, problem: str, steps: int = 5, context: str = "") -> Dict[str, Any]:
        """
        Perform multi-step reasoning on a problem.
        
        Args:
            problem: Problem or question to solve
            steps: Number of reasoning steps
            context: Additional context for reasoning
            
        Returns:
            Dict containing reasoning results
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize agent")
        
        start_time = time.time()
        
        try:
            # Simulate multi-step reasoning
            reasoning_chain = []
            current_thought = problem
            
            for i in range(steps):
                step_thought = f"Step {i+1}: Analyzing '{current_thought}'"
                if context:
                    step_thought += f" (Context: {context})"
                
                # Simulate reasoning progression
                if "calculate" in problem.lower() or "compute" in problem.lower():
                    next_thought = f"Performing calculations based on step {i+1}"
                elif "design" in problem.lower() or "create" in problem.lower():
                    next_thought = f"Developing design concepts from step {i+1}"
                elif "explain" in problem.lower() or "describe" in problem.lower():
                    next_thought = f"Elaborating explanation from step {i+1}"
                else:
                    next_thought = f"Building upon insights from step {i+1}"
                
                reasoning_chain.append({
                    "step": i + 1,
                    "thought": step_thought,
                    "insight": f"Intermediate conclusion from step {i+1}"
                })
                current_thought = next_thought
            
            final_conclusion = f"After {steps} steps of reasoning: {problem} has been analyzed and solved."
            
            execution_time = time.time() - start_time
            
            result = {
                "problem": problem,
                "context": context,
                "reasoning_steps": reasoning_chain,
                "final_conclusion": final_conclusion,
                "execution_time": execution_time,
                "success": True,
                "timestamp": time.time()
            }
            
            self.session_history.append({
                "tool": "reason",
                "input": {"problem": problem, "steps": steps, "context": context},
                "result": result,
                "timestamp": time.time()
            })
            
            print(f"🧠 Performed {steps}-step reasoning on: {problem}")
            return result
            
        except Exception as e:
            return {
                "problem": problem,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "success": False,
                "timestamp": time.time()
            }
    
    def plan(self, goal: str, constraints: str = "", resources: str = "") -> Dict[str, Any]:
        """
        Create a step-by-step execution plan.
        
        Args:
            goal: Goal or objective to achieve
            constraints: Constraints or limitations to consider
            resources: Available resources
            
        Returns:
            Dict containing execution plan
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize agent")
        
        start_time = time.time()
        
        try:
            # Simulate planning process
            phases = ["Analysis", "Design", "Implementation", "Testing", "Deployment"]
            plan_steps = []
            
            for i, phase in enumerate(phases):
                step = {
                    "phase": phase,
                    "step_number": i + 1,
                    "description": f"{phase.lower()} phase for achieving: {goal}",
                    "estimated_duration": f"{10 + i*5}-{20 + i*10} minutes",
                    "dependencies": [f"Step {i}" if i > 0 else "None"],
                    "resources_needed": resources.split(",") if resources else ["Basic tools"]
                }
                plan_steps.append(step)
            
            execution_time = time.time() - start_time
            
            result = {
                "goal": goal,
                "constraints": constraints,
                "resources": resources,
                "plan_steps": plan_steps,
                "total_estimated_time": f"{len(phases)*15}-{len(phases)*30} minutes",
                "execution_time": execution_time,
                "success": True,
                "timestamp": time.time()
            }
            
            self.session_history.append({
                "tool": "plan",
                "input": {"goal": goal, "constraints": constraints, "resources": resources},
                "result": result,
                "timestamp": time.time()
            })
            
            print(f"📋 Created execution plan for: {goal}")
            return result
            
        except Exception as e:
            return {
                "goal": goal,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "success": False,
                "timestamp": time.time()
            }
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent session history.
        
        Args:
            limit: Maximum number of history items to return
            
        Returns:
            List of session history items
        """
        return self.session_history[-limit:] if self.session_history else []
    
    def clear_session_history(self) -> None:
        """Clear session history."""
        self.session_history = []
        print("🗑️  Cleared session history")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this skill."""
        return self.system_prompt
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set a custom system prompt."""
        self.system_prompt = prompt
    
    def to_extension_def(self) -> ExtensionDef:
        """Convert to EGGUF ExtensionDef for side panel registration."""
        return ExtensionDef(
            name="agent",
            model_path="",  # Agent doesn't need a model file
            system_prompt=self.system_prompt,
            tools=self.available_tools,
            capabilities=[
                "terminal_access", "file_operations", "cloud_api", 
                "reasoning", "planning", "autonomous_execution"
            ]
        )
    
    @classmethod
    def from_extension_def(cls, extension_def: ExtensionDef) -> 'EGGUF_AGENT':
        """Create EGGUF_AGENT from ExtensionDef."""
        return cls(
            system_prompt=extension_def.system_prompt
        )