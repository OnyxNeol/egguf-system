"""
Tests for core EGGUF functionality.
"""

import json
import tempfile
import os
from pathlib import Path

from egguf import EGGUF, SidePanel, ExtensionDef, RoutingRules


def test_side_panel_creation():
    """Test creating and manipulating a SidePanel."""
    panel = SidePanel()
    
    # Check initial state
    assert len(panel.extensions) == 0
    assert panel.metadata["extension_count"] == 0
    
    # Add extension
    ext = ExtensionDef(
        name="test_ext",
        model_path="/tmp/test.gguf",
        system_prompt="Test prompt",
        tools={}
    )
    panel.add_extension(ext)
    
    assert len(panel.extensions) == 1
    assert panel.metadata["extension_count"] == 1
    assert "test_ext" in panel.extensions
    
    # Remove extension
    result = panel.remove_extension("test_ext")
    assert result is True
    assert len(panel.extensions) == 0
    assert panel.metadata["extension_count"] == 0
    
    # Try to remove non-existent extension
    result = panel.remove_extension("nonexistent")
    assert result is False


def test_extension_def_serialization():
    """Test ExtensionDef to/from dict conversion."""
    ext = ExtensionDef(
        name="vid",
        model_path="/tmp/vid.gguf",
        system_prompt="Video generation specialist",
        tools={
            "generate_video": {
                "description": "Generate video",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"}
                    }
                }
            }
        },
        capabilities=["video_generation"]
    )
    
    # Convert to dict
    ext_dict = ext.to_dict()
    assert ext_dict["name"] == "vid"
    assert ext_dict["model_path"] == "/tmp/vid.gguf"
    assert ext_dict["system_prompt"] == "Video generation specialist"
    assert ext_dict["capabilities"] == ["video_generation"]
    assert "generate_video" in ext_dict["tools"]
    
    # Convert back from dict
    ext_restored = ExtensionDef.from_dict(ext_dict)
    assert ext_restored.name == ext.name
    assert ext_restored.model_path == ext.model_path
    assert ext_restored.system_prompt == ext.system_prompt
    assert ext_restored.tools == ext.tools
    assert ext_restored.capabilities == ext.capabilities


def test_routing_rules():
    """Test RoutingRules parsing and matching."""
    rules = RoutingRules()
    
    # Test empty rules
    assert not rules.should_use_extension("vid")
    assert not rules.should_use_extension("img")
    
    # Test enabled extensions
    rules.enabled_extensions = ["vid", "img"]
    assert rules.should_use_extension("vid")
    assert rules.should_use_extension("img")
    assert not rules.should_use_extension("code")
    
    # Test disabled extensions
    rules.disabled_extensions = ["vid"]
    assert not rules.should_use_extension("vid")
    assert rules.should_use_extension("img")
    
    # Disabled takes precedence
    rules.enabled_extensions = ["vid", "img"]
    rules.disabled_extensions = ["vid"]
    assert not rules.should_use_extension("vid")  # Disabled wins
    assert rules.should_use_extension("img")
    
    # Test keyword extraction
    rules.task_keywords = {
        "vid": ["video", "motion", "animation"],
        "img": ["image", "picture", "photo"]
    }
    
    keywords = rules.extract_task_keywords("Create a video of a moving object")
    assert "vid" in keywords
    assert "video" in keywords["vid"] or "motion" in keywords["vid"]
    
    keywords = rules.extract_task_keywords("Draw a picture of a cat")
    assert "img" in keywords
    assert "picture" in keywords["img"] or "photo" in keywords["img"]
    
    keywords = rules.extract_task_keywords("Explain the theory of relativity")
    assert len(keywords) == 0  # No matches


def test_egguf_basic():
    """Test basic EGGUF initialization."""
    # Create a temporary GGUF file for testing
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
        # Write minimal valid GGUF header
        f.write(b'GGUF')  # Magic
        f.write(b'\x03\x00\x00\x00')  # Version 3 (little endian)
        f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')  # Tensor count = 0
        temp_path = f.name
    
    try:
        # Initialize EGGUF
        egguf = EGGUF(temp_path)
        assert egguf.model_path == Path(temp_path)
        assert len(egguf.side_panel.extensions) == 0
        
        # Add extension
        ext = ExtensionDef(
            name="test",
            model_path="/tmp/test.gguf",
            system_prompt="Test extension",
            tools={}
        )
        egguf.add_extension(ext)
        assert len(egguf.side_panel.extensions) == 1
        assert egguf.side_panel.has_extension("test")
        
        # Remove extension
        result = egguf.remove_extension("test")
        assert result is True
        assert len(egguf.side_panel.extensions) == 0
        
    finally:
        # Clean up
        os.unlink(temp_path)


def test_system_prompt_parsing():
    """Test SYSTEM prompt parsing."""
    egguf = EGGUF.__new__(EGGUF)  # Create instance without calling __init__
    
    # Test basic enable
    rules = egguf.parse_system_prompt("Enable vid,img")
    assert rules.enabled_extensions == ["vid", "img"]
    
    # Test enable with underscores
    rules = egguf.parse_system_prompt("Enable_vid Enable_img")
    assert "vid" in rules.enabled_extensions
    assert "img" in rules.enabled_extensions
    
    # Test only syntax
    rules = egguf.parse_system_prompt("Only vid")
    assert rules.enabled_extensions == ["vid"]
    
    # Test disable
    rules = egguf.parse_system_prompt("Disable img")
    assert rules.disabled_extensions == ["img"]
    
    # Test combined
    rules = egguf.parse_system_prompt("Enable vid,img,code Disable img")
    assert set(rules.enabled_extensions) == {"vid", "img", "code"}
    assert rules.disabled_extensions == ["img"]


if __name__ == "__main__":
    test_side_panel_creation()
    test_extension_def_serialization()
    test_routing_rules()
    test_egguf_basic()
    test_system_prompt_parsing()
    print("All core tests passed!")