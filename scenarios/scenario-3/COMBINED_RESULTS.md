# Arena Scenario-3 Combined Results

**Date**: 2026-03-13 16:17:26
**Scenario**: S3 (Multi-Agent Product Investigation)
**Iterations**: 2
**Total Runs**: 8

---

## Iteration Comparison

| Framework | Iter 1 | Iter 2 | Δ Correctness | Δ Latency | Consistency |
|-----------|--------|--------|---------------|-----------|-------------|
| Claude SDK (with Skill) | 85.0% | 85.0% | 0.0% | -2.27s | Stable |
| CrewAI (Multi-Agent) | 85.0% | 85.0% | 0.0% | +1.33s | Stable |
| AWS Strands (Multi-Agent) | 77.0% | 77.0% | 0.0% | +1.29s | Stable |
| Google ADK (Multi-Agent) | 77.0% | 77.0% | 0.0% | +6.59s | Stable |

---

## Detailed Comparison by Framework


### Claude SDK (with Skill)

**Iteration 1**:
- Correctness: 85.0% (range: 85.0-85.0%)
- Latency: 33.89s
- Tool Calls: 8.0
- Variance: 0.0

**Iteration 2**:
- Correctness: 85.0% (range: 85.0-85.0%)
- Latency: 31.62s
- Tool Calls: 8.0
- Variance: 0.0

**Analysis**: Stable - Highly consistent across iterations ✅

### CrewAI (Multi-Agent)

**Iteration 1**:
- Correctness: 85.0% (range: 85.0-85.0%)
- Latency: 82.49s
- Tool Calls: 10.0
- Variance: 0.0

**Iteration 2**:
- Correctness: 85.0% (range: 85.0-85.0%)
- Latency: 83.82s
- Tool Calls: 14.0
- Variance: 0.0

**Analysis**: Stable - Highly consistent across iterations ✅

### AWS Strands (Multi-Agent)

**Iteration 1**:
- Correctness: 77.0% (range: 77.0-77.0%)
- Latency: 49.92s
- Tool Calls: 12.0
- Variance: 0.0

**Iteration 2**:
- Correctness: 77.0% (range: 77.0-77.0%)
- Latency: 51.21s
- Tool Calls: 12.0
- Variance: 0.0

**Analysis**: Stable - Highly consistent across iterations ✅

### Google ADK (Multi-Agent)

**Iteration 1**:
- Correctness: 77.0% (range: 77.0-77.0%)
- Latency: 21.02s
- Tool Calls: 6.0
- Variance: 0.0

**Iteration 2**:
- Correctness: 77.0% (range: 77.0-77.0%)
- Latency: 27.61s
- Tool Calls: 10.0
- Variance: 0.0

**Analysis**: Stable - Highly consistent across iterations ✅

---

## Key Findings

1. **Consistency**: Frameworks with <2% variance show production readiness
2. **Performance**: Speed vs Correctness trade-offs visible
3. **Reliability**: All frameworks maintain 100% success rate across iterations