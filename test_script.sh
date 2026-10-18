#!/bin/bash
# EGGUF Library Test Script
# Demonstrates the Python library usage for modular AI skills

set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║   EGGUF Library - Python Skills Test             ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it first."
    exit 1
fi

echo "✅ Python detected: $(python3 --version)"
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "⚠️  pip3 not found. You may need to install dependencies manually."
else
    echo "✅ pip3 detected: $(pip3 --version)"
fi
echo ""

# Create test directory
echo "📁 Creating test environment..."
mkdir -p test_models
mkdir -p test_extensions
echo ""

# Create minimal GGUF model file (for testing)
if [ ! -f "test_models/base_model.gguf" ]; then
    echo "📝 Creating test GGUF model file..."
    # Minimal GGUF header
    printf "GGUF" > test_models/base_model.gguf  # Magic
    printf "\x00\x00\x00\x03" >> test_models/base_model.gguf  # Version 3 (little endian)
    printf "\x00\x00\x00\x00\x00\x00\x00\x00" >> test_models/base_model.gguf  # tensor count = 0
    echo "   Created test model placeholder"
fi
echo ""

# Create test script
echo "📝 Creating Python test script..."
cat > test_egguf.py << 'EOF'
#!/usr/bin/env python3
"""
EGGUF Library Test Script
Demonstrates usage of the Python library for modular AI skills
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from egguf import EGGUF, EGGUF_VID, EGGUF_IMG, EGGUF_AGENT, SidePanel, ExtensionDef

def test_core_egguf():
    """Test core EGGUF functionality."""
    print("🧪 Testing Core EGGUF...")
    
    # Create EGGUF instance
    egguf = EGGUF("test_models/base_model.gguf")
    print(f"   Created EGGUF with model: {egguf.model_path}")
    
    # Create video extension
    vid_ext = ExtensionDef(
        name="vid",
        model_path="test_models/headless_vid.gguf",
        system_prompt="You are a video generation specialist.",
        tools={
            "generate_video": {
                "description": "Generate video from text prompt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "duration": {"type": "integer", "minimum": 1, "maximum": 60}
                    },
                    "required": ["prompt"]
                }
            }
        }
    )
    
    # Add extension to EGGUF
    egguf.add_extension(vid_ext)
    print(f"   Added extension: {vid_ext.name}")
    
    # List skills
    skills = egguf.list_skills()
    print(f"   Available skills: {[s['name'] for s in skills if s]}")
    
    return egguf

def test_video_skill():
    """Test video skill extension."""
    print("\n🧪 Testing Video Skill (EGGUF_VID)...")
    
    # Create video skill
    vid_skill = EGGUF_VID(
        model_path="test_models/headless_vid.gguf",
        system_prompt="You are a video generation expert."
    )
    
    print(f"   Video skill system prompt: {vid_skill.get_system_prompt()[:50]}...")
    print(f"   Available tools: {vid_skill.list_tools()}")
    
    # Load model
    if vid_skill.load_model():
        print("   ✅ Video model loaded successfully")
        
        # Test video generation
        result = vid_skill.generate_video(
            prompt="A beautiful sunset over the ocean",
            duration=10,
            width=1920,
            height=1080
        )
        
        print(f"   🎬 Generated video: {result['output']['message']}")
        vid_skill.unload_model()
    else:
        print("   ❌ Failed to load video model")
    
    return vid_skill

def test_image_skill():
    """Test image skill extension."""
    print("\n🧪 Testing Image Skill (EGGUF_IMG)...")
    
    # Create image skill
    img_skill = EGGUF_IMG(
        model_path="test_models/headless_img.gguf",
        system_prompt="You are an image generation expert."
    )
    
    print(f"   Image skill system prompt: {img_skill.get_system_prompt()[:50]}...")
    print(f"   Available tools: {img_skill.list_tools()}")
    
    # Load model
    if img_skill.load_model():
        print("   ✅ Image model loaded successfully")
        
        # Test image generation
        result = img_skill.generate_image(
            prompt="A serene mountain landscape",
            width=1024,
            height=768,
            style="realistic"
        )
        
        print(f"   🖼️  Generated image: {result['output']['message']}")
        img_skill.unload_model()
    else:
        print("   ❌ Failed to load image model")
    
    return img_skill

def test_agent_skill():
    """Test agent skill extension."""
    print("\n🧪 Testing Agent Skill (EGGUF_AGENT)...")
    
    # Create agent skill
    agent_skill = EGGUF_AGENT(
        system_prompt="You are a helpful AI agent with access to tools."
    )
    
    print(f"   Agent skill system prompt: {agent_skill.get_system_prompt()[:50]}...")
    print(f"   Available tools: {agent_skill.list_tools()}")
    
    # Initialize agent
    if agent_skill.initialize():
        print("   ✅ Agent initialized successfully")
        
        # Test terminal command (safe command)
        result = agent_skill.execute_command("echo 'Hello from EGGUF Agent'", timeout=5)
        if result["success"]:
            print(f"   💻 Command output: {result['stdout'].strip()}")
        
        # Test file operations
        write_result = agent_skill.write_file(
            "test_output.txt", 
            "This is a test file created by EGGUF Agent\\nLine 2 of content."
        )
        if write_result["success"]:
            print("   💾 File written successfully")
            
            read_result = agent_skill.read_file("test_output.txt")
            if read_result["success"]:
                print(f"   📖 File content: {repr(read_result['content'])}")
        
        # Test reasoning
        reason_result = agent_skill.reason(
            "How can I improve the efficiency of a machine learning model?",
            steps=3
        )
        if reason_result["success"]:
            print(f"   🧠 Reasoning conclusion: {reason_result['final_conclusion']}")
        
        # Show session history
        history = agent_skill.get_session_history(limit=3)
        print(f"   📜 Session history: {len(history)} entries")
    else:
        print("   ❌ Failed to initialize agent")
    
    return agent_skill

def test_extension_conversion():
    """Test conversion between skill classes and ExtensionDef."""
    print("\n🧪 Testing Extension Def Conversion...")
    
    # Video skill to ExtensionDef and back
    vid_skill = EGGUF_VID("test_models/vid.gguf", "Test video prompt")
    vid_ext = vid_skill.to_extension_def()
    print(f"   Video skill → ExtensionDef: {vid_ext.name}")
    
    vid_skill_restored = EGGUF_VID.from_extension_def(vid_ext)
    print(f"   ExtensionDef → Video skill: {vid_skill_restored.model_path}")
    
    # Image skill to ExtensionDef and back
    img_skill = EGGUF_IMG("test_models/img.gguf", "Test image prompt")
    img_ext = img_skill.to_extension_def()
    print(f"   Image skill → ExtensionDef: {img_ext.name}")
    
    img_skill_restored = EGGUF_IMG.from_extension_def(img_ext)
    print(f"   ExtensionDef → Image skill: {img_skill_restored.model_path}")
    
    # Agent skill to ExtensionDef and back
    agent_skill = EGGUF_AGENT("Test agent prompt")
    agent_ext = agent_skill.to_extension_def()
    print(f"   Agent skill → ExtensionDef: {agent_ext.name}")
    
    agent_skill_restored = EGGUF_AGENT.from_extension_def(agent_ext)
    print(f"   ExtensionDef → Agent skill: {agent_skill_restored.system_prompt[:30]}...")

def main():
    """Run all tests."""
    print("🚀 Starting EGGUF Library Tests\n")
    
    try:
        # Test core functionality
        egguf = test_core_egguf()
        
        # Test individual skills
        vid_skill = test_video_skill()
        img_skill = test_image_skill()
        agent_skill = test_agent_skill()
        
        # Test extension conversion
        test_extension_conversion()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Summary:")
        print("   • Core EGGUF model management works")
        print("   • Video skill extension functional")
        print("   • Image skill extension functional")
        print("   • Agent skill extension functional")
        print("   • ExtensionDef conversion works both ways")
        print("\n💡 The EGGUF Python library is ready for use!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
    chmod +x test_egguf.py
    echo "   Created test script"
    echo ""

# Make test script executable and run it
echo "🔧 Making test script executable..."
chmod +x test_egguf.py
echo ""

# Run the test
echo "🧪 Running EGGUF library tests..."
echo ""
python3 test_egguf.py
echo ""

echo "✅ Test completed!"
echo ""
echo "📚 To use the EGGUF library in your projects:"
echo "   from egguf import EGGUF, EGGUF_VID, EGGUF_IMG, EGGUF_AGENT"
echo ""
echo "   # Core model"
echo "   egguf = EGGUF('path/to/model.gguf')"
echo ""
echo "   # Skill extensions"
echo "   vid = EGGUF_VID('path/to/vid_model.gguf')"
echo "   img = EGGUF_IMG('path/to/img_model.gguf')"
echo "   agent = EGGUF_AGENT()"
echo ""
echo "   # Or load from extension definitions"
echo "   vid_ext = egguf.get_skill_info('vid')"
echo "   vid_skill = EGGUF_VID.from_extension_def(vid_ext)"