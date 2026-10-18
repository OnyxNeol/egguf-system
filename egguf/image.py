"""
Image skill extension for EGGUF.

This module provides the EGGUF_IMG class for image generation and processing skills.
"""

from typing import Dict, Any, Optional
from pathlib import Path


class EGGUF_IMG:
    """
    Image skill extension for EGGUF models.
    
    Provides image generation and manipulation capabilities for EGGUF-enabled AI systems.
    """
    
    def __init__(self, model_path: str, system_prompt: str = ""):
        """
        Initialize image skill.
        
        Args:
            model_path: Path to headless image GGUF model
            system_prompt: System prompt for image generation
        """
        self.model_path = Path(model_path)
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.available_tools = self._get_available_tools()
        self.is_loaded = False
        self.model_data = None
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for image generation."""
        return (
            "You are an image generation expert. When users request pictures, artwork, "
            "or visual content, use the generate_image tool with descriptive prompts. "
            "You can generate images from text descriptions with customizable dimensions, "
            "style, and quality settings."
        )
    
    def _get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get available image tools."""
        return {
            "generate_image": {
                "description": "Generate image from text prompt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Detailed description of the image to generate"
                        },
                        "width": {
                            "type": "integer",
                            "minimum": 256,
                            "maximum": 1024,
                            "default": 512,
                            "description": "Image width in pixels"
                        },
                        "height": {
                            "type": "integer",
                            "minimum": 256,
                            "maximum": 1024,
                            "default": 512,
                            "description": "Image height in pixels"
                        },
                        "style": {
                            "type": "string",
                            "default": "photorealistic",
                            "description": "Artistic style (e.g., 'photorealistic', 'watercolor', 'anime')"
                        },
                        "quality": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 85,
                            "description": "Image quality (1-100)"
                        }
                    },
                    "required": ["prompt"]
                },
                "gateway": "local"  # or API endpoint
            },
            "modify_image": {
                "description": "Modify existing image",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string"},
                        "action": {
                            "type": "string",
                            "description": "Action to perform (e.g., 'resize', 'crop', 'enhance', 'filter')",
                            "default": "enhance"
                        },
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "width": {"type": "integer", "default": 512},
                                "height": {"type": "integer", "default": 512},
                                "crop_x": {"type": "integer", "default": 0},
                                "crop_y": {"type": "integer", "default": 0},
                                "contrast": {"type": "float", "default": 1.0},
                                "brightness": {"type": "float", "default": 1.0},
                                "saturation": {"type": "float", "default": 1.0}
                            },
                            "required": ["image_path"]
                        },
                        "output_path": {"type": "string", "required": True}
                    },
                    "required": ["image_path"]
                },
                "gateway": "local"
            },
            "edit_image": {
                "description": "Edit image with various operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string"},
                        "action": {"type": "string", "default": "enhance"},
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "width": {"type": "integer"},
                                "height": {"type": "integer"},
                                "crop_x": {"type": "integer"},
                                "crop_y": {"type": "integer"},
                                "contrast": {"type": "float"},
                                "brightness": {"type": "float"},
                                "saturation": {"type": "float"}
                            },
                            "required": ["image_path"]
                        },
                        "output_path": {"type": "string", "required": True}
                    },
                    "required": ["image_path"]
                },
                "gateway": "local"
            }
        }
    
    def load_model(self) -> bool:
        """
        Load the headless image model.
        
        Returns:
            bool: True if model loaded successfully
        """
        if self.is_loaded:
            return True
        
        try:
            self.model_data = {
                "path": str(self.model_path),
                "type": "image_model",
                "loaded_at": "2024-01-01T00:00:00Z",
                "capabilities": list(self.available_tools.keys())
            }
            self.is_loaded = True
            print(f"✅ Loaded image model: {self.model_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to load image model: {e}")
            return False
    
    def unload_model(self) -> None:
        """Unload the image model to free memory."""
        self.model_data = None
        self.is_loaded = False
        print(f"🗑️  Unloaded image model: {self.model_path}")
    
    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate image from text prompt.
        
        Args:
            prompt: Text description of image to generate
            **kwargs: Additional parameters (width, height, style, quality, etc.)
            
        Returns:
            Dict containing generation results
        """
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError("Failed to load image model")
        
        tool_schema = self.available_tools["generate_image"]
        params = self._validate_parameters(prompt, kwargs, tool_schema)
        
        result = self._execute_image_generation(params)
        
        return {
            "tool": "generate_image",
            "input": {"prompt": prompt, **kwargs},
            "parameters": params,
            "output": result,
            "model_used": str(self.model_path)
        }
    
    def _validate_parameters(self, prompt: str, kwargs: Dict[str, Any], 
                           tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize parameters."""
        params = {"prompt": prompt}
        defaults = tool_schema["parameters"].get("properties", {})
        
        for param_name, param_def in defaults.items():
            if param_name in kwargs:
                params[param_name] = kwargs[param_name]
            elif "default" in param_def:
                params[param_name] = param_def["default"]
        
        return params
    
    def _execute_image_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute image generation (simulated)."""
        return {
            "image_id": f"img_{hash(params['prompt'])}",
            "width": params["width"],
            "height": params["height"],
            "style": params.get("style", "photorealistic"),
            "quality": params.get("quality", 85),
            "status": "completed",
            "message": f"Generated image based on: {params['prompt']}"
        }
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool definition by name."""
        return self.available_tools.get(tool_name)
    
    def list_tools(self) -> list:
        """List all available tools."""
        return list(self.available_tools.keys())
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this skill."""
        return self.system_prompt
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set a custom system prompt."""
        self.system_prompt = prompt
    
    def to_extension_def(self) -> 'ExtensionDef':
        """Convert to EGGUF ExtensionDef for side panel registration."""
        from .core import ExtensionDef
        return ExtensionDef(
            name="img",
            model_path=str(self.model_path),
            system_prompt=self.system_prompt,
            tools=self.available_tools,
            capabilities=["image_generation", "image_editing", "visual_analysis"]
        )
    
    @classmethod
    def from_extension_def(cls, extension_def: 'ExtensionDef') -> 'EGGUF_IMG':
        """Create EGGUF_IMG from ExtensionDef."""
        return cls(
            model_path=extension_def.model_path,
            system_prompt=extension_def.system_prompt
        )