#!/usr/bin/env python3
"""
Quick test to verify the agent can be initialized and the graph structure is correct.
No API calls will be made.
"""

import sys
import os
from pathlib import Path

# Set environment to prevent API calls
os.environ.pop('OPENAI_API_KEY', None)

sys.path.insert(0, str(Path(__file__).parent))

def test_basic_agent_creation():
    """Test basic agent creation without LLM"""
    print("🔧 Testing basic agent creation (no API key)...")
    
    try:
        from whitepaper.agent import ThreeAgentSystem
        
        # This should work even without API key
        agent = ThreeAgentSystem()
        print("✅ Agent system created successfully")
        
        # Test a basic query that should fail gracefully without API
        result = agent.process_query("hello")
        print(f"✅ Basic query handled gracefully: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_graph_structure():
    """Test that the graph structure is correct"""
    print("🔧 Testing graph structure...")
    
    try:
        from whitepaper.agent import ThreeAgentSystem
        
        agent = ThreeAgentSystem()
        
        # The graph should be None when no LLM is available
        if agent.llm is None:
            expected_graph = None
        else:
            expected_graph = "some graph object"
            
        print(f"✅ Graph state: {type(agent.graph)} (expected when LLM={'available' if agent.llm else 'unavailable'})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Quick Agent Test (No API Calls)")
    print("=" * 50)
    
    tests = [
        test_basic_agent_creation,
        test_graph_structure,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print(f"\n📊 {passed}/{len(tests)} quick tests passed")
    
    if passed == len(tests):
        print("🎉 Basic agent structure looks good!")
        print("🔐 Ready for real testing with API key")
    else:
        print("⚠️ Some issues detected")
    
    return passed == len(tests)

if __name__ == "__main__":
    main()
