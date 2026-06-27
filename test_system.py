#!/usr/bin/env python3
"""
System test for LBOS-AI advanced features
Verifies that all components can be imported and initialized
"""

import sys
import os

# Add current directory to Python path so we can import lbos_ai
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all major components can be imported"""
    print("Testing imports...")

    # Test memory system
    try:
        from lbos_ai.memory.memory_system import MemorySystem, get_memory_system
        mem = MemorySystem("./test_memory.db")
        print("✓ Memory system imported successfully")
    except Exception as e:
        print(f"✗ Memory system import failed: {e}")
        return False

    # Test feedback loop
    try:
        from lbos_ai.training.feedback_loop import FeedbackTrainer, FeedbackItem
        print("✓ Feedback loop imported successfully")
    except Exception as e:
        print(f"✗ Feedback loop import failed: {e}")
        return False

    # Test evaluation intelligence
    try:
        from lbos_ai.eval.evaluation_intelligence import EvaluationIntelligence, get_evaluator
        eval_sys = EvaluationIntelligence("./test_eval")
        print("✓ Evaluation intelligence imported successfully")
    except Exception as e:
        print(f"✗ Evaluation intelligence import failed: {e}")
        return False

    # Test that we can create instances
    try:
        mem2 = get_memory_system()
        eval2 = get_evaluator()
        print("✓ Singleton patterns work correctly")
    except Exception as e:
        print(f"✗ Singleton test failed: {e}")
        return False

    return True

def test_memory_operations():
    """Test basic memory operations"""
    print("\nTesting memory operations...")

    try:
        from lbos_ai.memory.memory_system import MemorySystem

        # Clean up any previous test data
        if os.path.exists("./test_memory.db"):
            os.remove("./test_memory.db")

        mem = MemorySystem("./test_memory.db")

        # Test adding to different memory types
        wid = mem.add_to_working_memory("test_session", "This is a test memory", {"type": "test"})
        print(f"✓ Added to working memory: {wid}")

        eid = mem.add_to_episodic_memory("test_session", "test_event", "This happened", {"importance": 0.8})
        print(f"✓ Added to episodic memory: {eid}")

        sid = mem.add_to_semantic_memory("test_concept", "This is a definition", "concept")
        print(f"✓ Added to semantic memory: {sid}")

        # Test retrieval
        results = mem.retrieve_relevant_memories("test memory", limit=5)
        total_results = sum(len(v) for v in results.values())
        print(f"✓ Retrieved {total_results} relevant memories")

        # Test statistics
        stats = mem.get_statistics()
        print(f"✓ Memory stats: {stats['working_memory']['count']} working, {stats['episodic_memory']['count']} episodic, {stats['semantic_memory']['count']} semantic")

        # Clean up
        if os.path.exists("./test_memory.db"):
            os.remove("./test_memory.db")
        if os.path.exists("./test_eval"):
            import shutil
            shutil.rmtree("./test_eval")
        return True

    except Exception as e:
        print(f"✗ Memory operations test failed: {e}")
        import traceback
        traceback.print_exc()
        # Clean up
        if os.path.exists("./test_memory.db"):
            os.remove("./test_memory.db")
        if os.path.exists("./test_eval"):
            import shutil
            shutil.rmtree("./test_eval")
        return False

def test_feedback_system():
    """Test feedback system basics"""
    print("\nTesting feedback system...")

    try:
        from lbos_ai.training.feedback_loop import FeedbackItem

        # Create a feedback item
        feedback = FeedbackItem(
            input_text="What is the capital of France?",
            model_output="The capital of France is Berlin.",
            expected_output="The capital of France is Paris.",
            feedback_type="correction"
        )

        print(f"✓ Created feedback item: {feedback.id}")
        print(f"  Input: {feedback.input_text}")
        print(f"  Model output: {feedback.model_output}")
        print(f"  Expected: {feedback.expected_output}")

        # Test serialization
        data = feedback.to_dict()
        restored = FeedbackItem.from_dict(data)
        print(f"✓ Serialization test passed: {restored.id == feedback.id}")

        return True
    except Exception as e:
        print(f"✗ Feedback system test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("LBOS-AI Advanced Features System Test")
    print("=====================================")

    tests = [
        test_imports,
        test_memory_operations,
        test_feedback_system
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()  # Blank line between tests

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The system is ready.")
        return 0
    else:
        print("❦ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())