# Parallel Benchmark Iteration 2 - Complete Results

**Date**: 2026-03-13 10:58:09
**Iteration**: 2
**Execution Mode**: Parallel (all frameworks simultaneously)
**Total Wall-Clock Time**: 276.88s
**Scenarios**: S1, S1b, S1c, S2 (all scenarios)
**Repetitions**: K=3 per scenario
**Total Runs**: 48

---

## Executive Summary

This is the **definitive benchmark run** with:
- ✅ **Parallel execution** (no position bias)
- ✅ **All scenarios** (S1-S2 combined)
- ✅ **True performance** measurements

### Overall Winner: 🥇 Claude Sdk
- **Overall Correctness**: 88.58%
- **Overall Latency**: 20.98s
- **Overall Consistency**: 100%

---

## Complete Framework Rankings

### By Overall Correctness (All Scenarios)

| Rank | Framework | Correctness | Latency | Consistency | Cost | LoC | CC |
|------|-----------|-------------|---------|-------------|------|-----|-----|
| 🥇 | **Claude Sdk** | 88.58% | 20.98s | 100% | $0.0384 | 72 | 3.0 |
| 🥈 | **Aws Strands** | 84.25% | 17.41s | 75% | $0.00* | 140 | 2.2 |
| 🥉 | **Google Adk** | 83.67% | 14.65s | 50% | $0.00* | 158 | 2.0 |
| 4. | **Crewai** | 79.25% | 17.00s | 75% | $0.0916 | 145 | 1.6 |

*Note: $0.00* indicates token tracking not available

---

## Per-Scenario Performance

### S1: Damaged Laptop Refund

| Framework | Correctness | Latency | Consistency |
|-----------|-------------|---------|-------------|
| Claude Sdk | 100.00% | 19.00s | 100% |
| Aws Strands | 100.00% | 16.96s | 100% |
| Google Adk | 100.00% | 14.32s | 100% |
| Crewai | 100.00% | 17.83s | 100% |

### S1b: Shipping Address Change

| Framework | Correctness | Latency | Consistency |
|-----------|-------------|---------|-------------|
| Claude Sdk | 100.00% | 17.12s | 100% |
| Aws Strands | 100.00% | 14.15s | 100% |
| Google Adk | 89.00% | 11.77s | 0% |
| Crewai | 67.00% | 13.24s | 0% |

### S1c: Billing Dispute Escalation

| Framework | Correctness | Latency | Consistency |
|-----------|-------------|---------|-------------|
| Claude Sdk | 75.00% | 18.04s | 100% |
| Aws Strands | 75.00% | 14.59s | 100% |
| Google Adk | 75.00% | 13.93s | 100% |
| Crewai | 75.00% | 17.85s | 100% |

### S2: The Frustrated Premium Customer (Complex)

| Framework | Correctness | Latency | Consistency |
|-----------|-------------|---------|-------------|
| Claude Sdk | 79.33% | 29.75s | 100% |
| Crewai | 75.00% | 19.09s | 100% |
| Google Adk | 70.67% | 18.58s | 0% |
| Aws Strands | 62.00% | 23.93s | 0% |

---

## Key Advantages of This Run

### 1. No Position Bias ✅
- All frameworks executed **simultaneously**
- Eliminates sequential testing artifacts
- True parallel performance comparison

### 2. Complete Coverage ✅
- All 4 scenarios tested (S1-S2)
- Simple + Complex scenarios
- Comprehensive framework evaluation

### 3. Fair Comparison ✅
- Identical execution conditions
- Same system resources
- Same API load

---

## Comparison with Sequential Runs

| Metric | Sequential Runs | This Parallel Run |
|--------|----------------|-------------------|
| Position Bias | ⚠️ 20% variance | ✅ Eliminated |
| Latency Validity | ❌ Confounded | ✅ Valid |
| Total Time | ~15-20 min | ~5-7 min |
| Fairness | ⚠️ Order-dependent | ✅ Equal conditions |

---

## Production Recommendations

### 🥇 Claude Sdk
- **Overall Correctness**: 88.58%
- **Average Latency**: 20.98s
- **Consistency**: 100%

**Performance by Complexity**:
- Simple scenarios (S1-S1c): 91.67%
- Complex scenarios (S2): 79.33%

### 🥈 Aws Strands
- **Overall Correctness**: 84.25%
- **Average Latency**: 17.41s
- **Consistency**: 75%

**Performance by Complexity**:
- Simple scenarios (S1-S1c): 91.67%
- Complex scenarios (S2): 62.00%

### 🥉 Google Adk
- **Overall Correctness**: 83.67%
- **Average Latency**: 14.65s
- **Consistency**: 50%

**Performance by Complexity**:
- Simple scenarios (S1-S1c): 88.00%
- Complex scenarios (S2): 70.67%

---

**Report Generated**: 2026-03-13 10:58:09
**Status**: ✅ Complete
**Total Frameworks**: 4
**Total Scenarios**: 4 (S1-S2)
**Total Runs**: 48
