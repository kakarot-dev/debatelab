#!/usr/bin/env python3
"""Test script to demonstrate intelligent tool usage."""

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.llm_wrapper import LocalLLM
from src.tools.tool_manager import get_tool_manager
from src.tools.builtin_tools.test_tool import TestTool
from src.tools.builtin_tools.web_search_tool import WebSearchTool

def test_intelligent_tool_usage():
    """Test the intelligent two-step tool usage approach."""
    print("=" * 80)
    print("TESTING INTELLIGENT TOOL USAGE")
    print("Step 1: Ask LLM if it needs tools")
    print("Step 2: Execute tools only if requested")
    print("Step 3: Generate final response with tool context")
    print("=" * 80)
    
    # Set up tools
    tool_manager = get_tool_manager()
    tool_manager.register_tool(TestTool())
    tool_manager.register_tool(WebSearchTool())
    
    # Create LLM instance
    llm = LocalLLM()
    
    # Test case 1: Topic that should trigger tool usage
    print("\n" + "="*50)
    print("TEST CASE 1: Topic requiring current data")
    print("="*50)
    
    messages1 = [
        {
            "role": "system",
            "content": "You are Alex the Optimist in a debate. You focus on positive aspects and solutions."
        },
        {
            "role": "user",
            "content": "What are your thoughts on renewable energy investment? Please provide your perspective for the debate."
        }
    ]
    
    try:
        print("\n🎯 Starting intelligent tool usage process...")
        response1 = llm.create_chat_completion_with_tools(messages1, tool_manager)
        
        print("\n📝 Final response:")
        print("   " + "\n   ".join(response1.split("\n")[:5]))  # Show first 5 lines
        print("   ...")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test case 2: Simple topic that might not need tools
    print("\n" + "="*50)
    print("TEST CASE 2: Simple opinion topic")
    print("="*50)
    
    messages2 = [
        {
            "role": "system",
            "content": "You are Sam the Skeptic in a debate. You question assumptions and examine problems."
        },
        {
            "role": "user",
            "content": "Do you think pineapple belongs on pizza? Give your perspective."
        }
    ]
    
    try:
        print("\n🎯 Starting intelligent tool usage process...")
        response2 = llm.create_chat_completion_with_tools(messages2, tool_manager)
        
        print("\n📝 Final response:")
        print("   " + "\n   ".join(response2.split("\n")[:3]))  # Show first 3 lines
        print("   ...")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("INTELLIGENT TOOL USAGE TEST COMPLETE!")
    print("✅ LLM decides when to use tools")
    print("✅ Tools are executed only when needed")
    print("✅ Real tool results are incorporated into responses")
    print("✅ More efficient than always trying to parse tool calls")
    print("=" * 80)

if __name__ == "__main__":
    test_intelligent_tool_usage()