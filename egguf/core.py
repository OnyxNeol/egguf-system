"""
Core EGGUF implementation for modular AI skills.

This module provides the main EGGUF class that manages the base GGUF model
and the side-panel skill registry.
"""

import json
import os
import struct
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Type aliases for better code readability
ExtensionName = str
ModelPath = str
SystemPrompt = str
ToolName = str
GatewayURL = str


class ExtensionDef:
    """Definition of a skill extension in the EGGUF side panel."""
    
    def __init__(self, name: ExtensionName, model_path: ModelPath, 
                 system_prompt: SystemPrompt, tools: Dict[str, Dict[str, Any]],
                 capabilities: Optional[List[str]] = None):
        self.name = name
        self.model_path = model_path
        self.system_prompt = system_prompt
        self.tools = tools
        self.capabilities = capabilities or []
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "model_path": self.model_path,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "capabilities": self.capabilities,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtensionDef':
        """Create ExtensionDef from dictionary."""
        return cls(
            name=data["name"],
            model_path=data["model_path"],
            system_prompt=data["system_prompt"],
            tools=data["tools"],
            capabilities=data.get("capabilities", [])
        )
    
    def has_tool(self, tool_name: ToolName) -> bool:
        """Check if extension has a specific tool."""
        return tool_name in self.tools
    
    def get_tool(self, tool_name: ToolName) -> Optional[Dict[str, Any]]:
        """Get tool definition by name."""
        return self.tools.get(tool_name)
class SidePanel:
    """Side-panel metadata attached to EGGUF model."""
    
    def __init__(self, extensions: Optional[Dict[ExtensionName, ExtensionDef]] = None):
        self.extensions = extensions or {}
        self.metadata = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "extension_count": len(self.extensions)
        }
    
    def add_extension(self, extension: ExtensionDef) -> None:
        """Add an extension to the side panel."""
        self.extensions[extension.name] = extension
        self.metadata["extension_count"] = len(self.extensions)
    
    def remove_extension(self, name: ExtensionName) -> bool:
        """Remove an extension by name. Returns True if removed."""
        if name in self.extensions:
            del self.extensions[name]
            self.metadata["extension_count"] = len(self.extensions)
            return True
        return False
    
    def get_extension(self, name: ExtensionName) -> Optional[ExtensionDef]:
        """Get extension by name."""
        return self.extensions.get(name)
    
    def get_extension_names(self) -> List[ExtensionName]:
        """Get all extension names."""
        return list(self.extensions.keys())
    
    def has_extension(self, name: ExtensionName) -> bool:
        """Check if extension exists."""
        return name in self.extensions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "extensions": {name: ext.to_dict() for name, ext in self.extensions.items()},
            "metadata": self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SidePanel':
        """Create SidePanel from dictionary."""
        side_panel = cls()
        side_panel.metadata = data.get("metadata", {})
        
        if "extensions" in data:
            for ext_data in data["extensions"].values():
                extension = ExtensionDef.from_dict(ext_data)
                side_panel.extensions[extension.name] = extension
        
        return side_panel
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SidePanel':
        """Create SidePanel from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
class RoutingRules:
    """Routing rules extracted from SYSTEM prompt."""
    
    def __init__(self, enabled_extensions: Optional[List[ExtensionName]] = None,
                 disabled_extensions: Optional[List[ExtensionName]] = None,
                 task_keywords: Optional[Dict[str, List[str]]] = None):
        self.enabled_extensions = enabled_extensions or []
        self.disabled_extensions = disabled_extensions or []
        self.task_keywords = task_keywords or {}
        self.custom_rules = {}
    
    def should_use_extension(self, extension_name: ExtensionName) -> bool:
        """Check if an extension should be used based on routing rules."""
        if extension_name in self.disabled_extensions:
            return False
        if self.enabled_extensions and extension_name in self.enabled_extensions:
            return True
        if not self.enabled_extensions:
            return False
        return False
    
    def extract_task_keywords(self, task: str) -> Dict[str, Any]:
        """Extract keywords from task for skill matching."""
        result = {}
        
        for skill, keywords in self.task_keywords.items():
            skill_matches = []
            for keyword in keywords:
                if keyword.lower() in task.lower():
                    skill_matches.append(keyword)
            
            if skill_matches:
                result[skill] = skill_matches
        
        return result
class EGGUF:
    """
    Core EGGUF model manager with skill extensions.
    
    Manages the base GGUF model and the side-panel skill registry.
    """
    
    # GGUF file format constants
    GGUF_MAGIC = b"GGUF"
    GGUF_VERSION = 3
    SIDE_PANEL_MARKER = b"EGGUF_SIDE_PANEL_DATA"
    
    def __init__(self, model_path: str, side_panel: Optional['SidePanel'] = None):
        self.model_path = Path(model_path)
        self.side_panel = side_panel or SidePanel()
        self.skill_instances: Dict[ExtensionName, Any] = {}
        self._validate_model_file()
        self._log_initialization()
    
    def _validate_model_file(self) -> None:
        """Validate that the model file exists and is a valid GGUF."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        with open(self.model_path, 'rb') as f:
            magic = f.read(4)
            if magic != self.GGUF_MAGIC:
                raise ValueError(f"Invalid GGUF magic: {magic}")
            
            version_bytes = f.read(4)
            if version_bytes:
                version = struct.unpack('<I', version_bytes)[0]
                if version != self.GGUF_VERSION:
                    print(f"Warning: Unsupported GGUF version: {version}")
    
    def _log_initialization(self) -> None:
        """Log initialization information."""
        print(f" Initialized EGGUF with model: {self.model_path}")
        print(f"   Registered skills: {len(self.side_panel.extensions)}")
        for name in self.side_panel.get_extension_names():
            print(f"     • {name}")
    
    def add_extension(self, extension: 'ExtensionDef') -> None:
        """Add a new skill extension to the model."""
        if self.side_panel.has_extension(extension.name):
            print(f"Warning: Extension '{extension.name}' already exists. Overwriting.")
        self.side_panel.add_extension(extension)
        print(f"   Added skill: {extension.name}")
    
    def remove_extension(self, name: ExtensionName) -> bool:
        """Remove a skill extension."""
        return self.side_panel.remove_extension(name)
    
    def load_skill(self, name: ExtensionName) -> Dict[str, Any]:
        """Load a skill extension instance."""
        extension = self.side_panel.get_extension(name)
        if not extension:
            raise ValueError(f"Skill not found: {name}")
        
        skill_instance = self._create_skill_instance(name, extension)
        self.skill_instances[name] = skill_instance
        print(f"   Loaded skill: {name}")
        return skill_instance
    
    def _create_skill_instance(self, name: ExtensionName, extension: 'ExtensionDef') -> Dict[str, Any]:
        """Create a skill instance from extension definition."""
        return {
            "name": name,
            "system_prompt": extension.system_prompt,
            "tools": extension.tools,
            "model_path": extension.model_path,
            "loaded": True
        }
    
    def parse_system_prompt(self, prompt: str) -> 'RoutingRules':
        """
        Parse SYSTEM prompt to extract routing rules.
        
        Examples:
        - "enable vid,img" -> enable vid and img skills
        - "enable_vid enable_img" -> enable vid and img skills
        - "only vid" -> enable only vid skill
        """
        rules = RoutingRules()
        
        prompt_lower = prompt.lower()
        
        if prompt_lower.startswith("enable "):
            skill_list = prompt[7:].strip()
            enabled = [s.strip() for s in skill_list.split(',')]
            rules.enabled_extensions = enabled
        
        for word in prompt_lower.split():
            if word.startswith("enable_"):
                skill_name = word[7:]
                if skill_name not in rules.enabled_extensions:
                    rules.enabled_extensions.append(skill_name)
        
        if "only " in prompt_lower:
            skill_list = prompt_lower[5:].strip()
            rules.enabled_extensions = [s.strip() for s in skill_list.split(',')]
        
        if "disable " in prompt_lower:
            disabled_list = prompt_lower[8:].strip()
            rules.disabled_extensions = [s.strip() for s in disabled_list.split(',')]
        
        print(f"   Parsed routing rules from SYSTEM prompt:")
        print(f"     Enabled extensions: {rules.enabled_extensions}")
        print(f"     Disabled extensions: {rules.disabled_extensions}")
        
        return rules
    
    def match_task_to_skills(self, task: str, routing_rules: 'RoutingRules') -> List[ExtensionName]:
        """
        Match task keywords to available skills based on routing rules.
        Returns list of skill names that should be activated.
        """
        matching_skills = []
        
        task_keywords = routing_rules.extract_task_keywords(task)
        
        for extension_name in self.side_panel.get_extension_names():
            if not routing_rules.should_use_extension(extension_name):
                continue
            
            extension = self.side_panel.get_extension(extension_name)
            if not extension:
                continue
            
            matched = False
            for skill in task_keywords:
                if extension_name in skill:
                    matched = True
                    break
            
            if matched:
                matching_skills.append(extension_name)
                print(f"   Matched skill '{extension_name}' to task: '{task}'")
        
        return matching_skills
    
    def execute_with_skills(self, system_prompt: str, task: str) -> Dict[str, Any]:
        """
        Execute task with skills based on SYSTEM prompt routing rules.
        Main entry point for skill execution.
        """
        print(f"📋 Executing task with skills:")
        print(f"   Task: '{task}'")
        print(f"   System Prompt: '{system_prompt}'")
        
        routing_rules = self.parse_system_prompt(system_prompt)
        active_skills = self.match_task_to_skills(task, routing_rules)
        result = self._execute_with_skills(task, active_skills)
        
        return result
    
    def _execute_with_skills(self, task: str, skills: List[ExtensionName]) -> Dict[str, Any]:
        """Execute task with specified skills."""
        if not skills:
            print(f"   [Base Model] Processing: {task}")
            return {
                "task": task,
                "used_skills": [],
                "output": f"🤖 [Base Model] Processing: {task}",
                "fallback": True
            }
        
        used_skills = []
        outputs = []
        
        for skill_name in skills:
            skill_instance = self.skill_instances.get(skill_name)
            if not skill_instance:
                print(f"   Warning: Skill '{skill_name}' not loaded. Attempting to load...")
                skill_instance = self.load_skill(skill_name)
            
            skill_result = self._execute_skill(task, skill_name, skill_instance)
            used_skills.append(skill_name)
            outputs.append(skill_result)
        
        combined_output = self._combine_skill_results(task, used_skills, outputs)
        
        return {
            "task": task,
            "used_skills": used_skills,
            "output": combined_output,
            "skills_executed": True
        }
    
    def _execute_skill(self, task: str, skill_name: ExtensionName, skill_instance: Any) -> Dict[str, Any]:
        """Execute a single skill."""
        extension = self.side_panel.get_extension(skill_name)
        if not extension:
            raise ValueError(f"Skill not found: {skill_name}")
        
        print(f"   [{skill_name} Skill] System Prompt: {extension.system_prompt}")
        
        tool_results = []
        
        for tool_name, tool_def in extension.tools.items():
            print(f"     → Executing tool '{tool_name}': {tool_def['description']}")
            
            params = self._extract_tool_parameters(task, tool_def)
            
            tool_result = {
                "tool": tool_name,
                "parameters": params,
                "result": self._simulate_tool_execution(tool_name, params),
                "gateway": tool_def.get("gateway", "unknown")
            }
            
            tool_results.append(tool_result)
        
        return {
            "skill": skill_name,
            "tools": tool_results,
            "combined_output": f"[{skill_name} Skill]: Processed '{task}' via {len(tool_results)} tools"
        }
    
    def _extract_tool_parameters(self, task: str, tool_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tool parameters from task based on tool schema."""
        params = {}
        
        if "parameters" in tool_def:
            for param_name, param_def in tool_def["parameters"].get("properties", {}).items():
                if param_name.lower() in task.lower():
                    params[param_name] = param_def
        
        return params
    
    def _simulate_tool_execution(self, tool_name: ToolName, params: Dict[str, Any]) -> str:
        """Simulate tool execution for demonstration."""
        results = {
            "generate_video": f"Created video with duration: {params.get('duration', 5)}s based on: {params.get('prompt', 'video prompt')}",
            "generate_image": f"Generated image {params.get('width', 512)}x{params.get('height', 512)} based on: {params.get('prompt', 'image prompt')}",
            "terminal_command": f"Executed command: {params.get('command', 'unknown command')}",
            "cloud_api": f"Called cloud API with params: {params}"
        }
        
        return results.get(tool_name, f"Executed tool: {tool_name}")
    
    def _combine_skill_results(self, task: str, skills: List[ExtensionName], 
                              skill_results: List[Dict[str, Any]]) -> str:
        """Combine results from multiple skills."""
        if not skill_results:
            return f"🤖 [Base Model] Processing: {task}"
        
        if len(skill_results) == 1:
            result = skill_results[0]
            return result.get("combined_output", f"Skill {skills[0]}: {result}")
        
        combined = "🤖 [Multi-Skill Execution]\n"
        for i, (skill, result) in enumerate(zip(skills, skill_results)):
            combined += f"   [{skill}]: {result.get('combined_output', 'Processed')}\n"
        
        return combined.strip()
    
    def save(self, output_path: Optional[str] = None) -> str:
        """Save EGGUF model with side panel to file."""
        if output_path is None:
            output_path = str(self.model_path.with_suffix('.egguf'))
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        side_panel_json = self.side_panel.to_json()
        
        saved_data = {
            "model_path": str(self.model_path),
            "side_panel": self.side_panel.to_dict(),
            "skill_instances": self.skill_instances,
            "version": "1.0",
            "created": datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(saved_data, f, indent=2)
        
        print(f"✅ EGGUF model saved to: {output_path}")
        return output_path
    
    def load(self, input_path: str) -> 'EGGUF':
        """Load EGGUF model from file."""
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"EGGUF file not found: {input_path}")
        
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        model_path = Path(data["model_path"])
        side_panel = SidePanel.from_dict(data["side_panel"])
        
        egguf = EGGUF(str(model_path), side_panel)
        egguf.skill_instances = data.get("skill_instances", {})
        
        print(f"✅ EGGUF model loaded from: {input_path}")
        return egguf
    
    def get_skill_info(self, name: ExtensionName) -> Optional[Dict[str, Any]]:
        """Get information about a specific skill."""
        extension = self.side_panel.get_extension(name)
        if not extension:
            return None
        
        return {
            "name": extension.name,
            "model_path": extension.model_path,
            "system_prompt": extension.system_prompt,
            "capabilities": extension.capabilities,
            "tools": extension.tools,
            "loaded": name in self.skill_instances
        }
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """List all available skills."""
        return [info for info in 
                [self.get_skill_info(name) for name in self.side_panel.get_extension_names()]
                if info is not None]