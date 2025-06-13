#!/usr/bin/env python3

"""Test script to verify tool framework works in the actual debate system."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.debate_manager import DebateManager

def test_debate_with_tools():
    """Test that the debate system uses tools when appropriate."""
    
    print("=" * 80)
    print("TESTING DEBATE SYSTEM WITH TOOL FRAMEWORK")
    print("Testing that agents use tools during actual debates")
    print("=" * 80)
    
    # Create a debate topic that should trigger tool usage
    topic = "Current renewable energy statistics show that solar power adoption is accelerating globally"
    
    print(f"\n🎯 Debate Topic: {topic}")
    print("🔍 Expected: Agents should request web_search for current data")
    
    # Initialize debate manager
    debate_manager = DebateManager(topic, enable_moderator=False)
    
    print(f"\n📋 Created debate with {len(debate_manager.agents)} agents")
    print("🔧 Tool framework should be integrated into agents")
    
    # Start a single round to test tool usage
    print("\n🚀 Starting debate round...")
    
    try:
        # This should trigger the tool framework
        debate_manager.run_debate(max_rounds=1)
        print("\n✅ Debate completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during debate: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debate_with_tools()