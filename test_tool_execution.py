#!/usr/bin/env python3

"""Test script to verify tool execution works when requested."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.llm_wrapper import get_llm
from src.tools.tool_manager import get_tool_manager
from src.tools.builtin_tools.test_tool import TestTool
from src.tools.builtin_tools.web_search_tool import WebSearchTool

def test_forced_tool_usage():
    """Test that tools are actually executed when the LLM requests them."""
    
    print("=" * 80)
    print("TESTING FORCED TOOL EXECUTION")
    print("Testing that tools are executed when explicitly requested")
    print("=" * 80)
    
    # Initialize components
    tool_manager = get_tool_manager()
    tool_manager.register_tool(TestTool())
    tool_manager.register_tool(WebSearchTool())
    llm = get_llm()
    
    # Create a message that should definitely trigger tool usage
    messages = [
        {
            "role": "system",
            "content": "You are a debate participant. You must use current data to support your arguments."
        },
        {
            "role": "user", 
            "content": """Topic: "Current renewable energy statistics show promising growth"

You MUST search for current renewable energy data to support your argument. This topic requires up-to-date statistics and facts that you cannot know without searching."""
        }
    ]
    
    print("\n🎯 Testing with explicit tool requirement...")
    print("📋 Topic: Current renewable energy statistics")
    print("🔍 Expected: LLM should request web_search tool")
    
    response = llm.create_chat_completion_with_tools(messages, tool_manager)
    
    print(f"\n📝 Final response:")
    print(f"   {response[:200]}...")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_forced_tool_usage()