# Scenario-3 Iteration 2 Summary

**Date**: 2026-03-13 16:16:03
**Scenario**: S3 (Multi-Agent Product Investigation)
**Repetitions**: 3 per framework
**Total Runs**: 12
**Total Time**: 594.07s

## Framework Performance

| Framework | Correctness | Latency | Tool Calls | Success Rate |
|-----------|-------------|---------|------------|-------------|
| Claude SDK (with Skill) | 85.0% | 32.21s | 8.0 | 100% |
| CrewAI (Multi-Agent) | 85.0% | 81.07s | 11.3 | 100% |
| Google ADK (Multi-Agent) | 79.7% | 25.06s | 7.7 | 100% |
| AWS Strands (Multi-Agent) | 77.0% | 50.68s | 12.0 | 100% |

## Key Findings

- Multi-agent coordination effectiveness varies by framework
- Tool call efficiency is critical for performance
- Context passing between agents impacts correctness
