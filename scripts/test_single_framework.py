#!/usr/bin/env python3
"""
Test a single framework for Scenario-3 (S3)

Usage:
    python scripts/test_single_framework.py claude_sdk
    python scripts/test_single_framework.py crewai
    python scripts/test_single_framework.py google_adk
    python scripts/test_single_framework.py aws_strands
    python scripts/test_single_framework.py langgraph
    python scripts/test_single_framework.py langchain
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arena.scenarios import SCENARIOS
from arena.evaluator import evaluate_scenario
from arena.frameworks.claude_sdk_agent import ClaudeSDKAdapter
from arena.frameworks.crewai_multiagent import CrewAIMultiAgent
from arena.frameworks.google_adk_multiagent import GoogleADKMultiAgent
from arena.frameworks.aws_strands_multiagent import AWSStrandsMultiAgent
from arena.frameworks.langgraph_multiagent import LangGraphMultiAgent
from arena.frameworks.langchain_multiagent import LangChainMultiAgent


FRAMEWORKS = {
    "claude_sdk": ("Claude SDK (with Skill)", ClaudeSDKAdapter),
    "crewai": ("CrewAI (Multi-Agent)", CrewAIMultiAgent),
    "google_adk": ("Google ADK (Multi-Agent)", GoogleADKMultiAgent),
    "aws_strands": ("AWS Strands (Multi-Agent)", AWSStrandsMultiAgent),
    "langgraph": ("LangGraph (Multi-Agent)", LangGraphMultiAgent),
    "langchain": ("LangChain (Multi-Agent)", LangChainMultiAgent)
}


def test_framework(framework_key: str):
    """Test a single framework."""
    if framework_key not in FRAMEWORKS:
        print(f"Unknown framework: {framework_key}")
        print(f"Available: {', '.join(FRAMEWORKS.keys())}")
        return

    framework_name, framework_class = FRAMEWORKS[framework_key]
    scenario_name = "S3"
    scenario = SCENARIOS[scenario_name]

    print("="*80)
    print(f"Testing: {framework_name}")
    print(f"Scenario: {scenario_name} (Multi-Agent Product Investigation)")
    print("="*80)

    # Initialize agent
    if framework_name == "Claude SDK (with Skill)":
        system_prompt = """You are a helpful AI assistant with access to customer service tools.
Help customers with their inquiries about orders, products, and account information."""
        agent = framework_class(system_prompt=system_prompt)
    else:
        agent = framework_class()

    try:
        print("\n🚀 Running agent...")

        # Run the agent
        result = agent.run(
            user_message=scenario["user_message"],
            customer_id=scenario["customer_id"]
        )

        # Evaluate correctness
        correctness_score, criteria_results = evaluate_scenario(
            scenario_id=scenario_name,
            tool_log=result.tool_calls,
            final_response=result.response
        )

        # Print results
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS")
        print(f"{'='*80}")
        print(f"Correctness:    {correctness_score:.1f}%")
        print(f"Latency:        {result.latency:.2f}s")
        print(f"Tool Calls:     {len(result.tool_calls)}")
        print(f"Tools Used:     {', '.join(set(result.tool_calls))}")
        print(f"\nToken Usage:")
        print(f"  Input:  {result.token_usage.get('input_tokens', 0):,}")
        print(f"  Output: {result.token_usage.get('output_tokens', 0):,}")

        print(f"\nCriteria Results:")
        passing = sum(1 for v in criteria_results.values() if v)
        total = len(criteria_results)
        print(f"  Passing: {passing}/{total}")

        for criterion, passed in criteria_results.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {criterion}")

        print(f"\nResponse Preview:")
        preview = result.response[:500] + "..." if len(result.response) > 500 else result.response
        print(preview)

        # Save result
        output_file = Path(f"test_results/{framework_key}_test.json")
        output_file.parent.mkdir(exist_ok=True)

        output_data = {
            "framework": framework_name,
            "scenario": scenario_name,
            "success": True,
            "correctness_score": correctness_score,
            "latency": result.latency,
            "tool_calls": result.tool_calls,
            "tool_count": len(result.tool_calls),
            "token_usage": result.token_usage,
            "criteria_results": criteria_results,
            "response": result.response,
            "metadata": result.metadata
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}")
        print(f"{'='*80}\n")

        return True

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ ERROR")
        print(f"{'='*80}")
        print(f"Framework: {framework_name}")
        print(f"Error: {str(e)}")
        print(f"\nTraceback:")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")

        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_single_framework.py <framework>")
        print(f"\nAvailable frameworks: {', '.join(FRAMEWORKS.keys())}")
        sys.exit(1)

    framework_key = sys.argv[1]
    success = test_framework(framework_key)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
