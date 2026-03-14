# Parallel Benchmark Iteration 1 - Complete Results

**Date**: 2026-03-13 10:46:05
**Iteration**: 1
**Execution Mode**: Parallel (all frameworks simultaneously)
**Total Wall-Clock Time**: 246.89s
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
- **Overall Latency**: 20.09s
- **Overall Consistency**: 100%

---

## Complete Framework Rankings

### By Overall Correctness (All Scenarios)

| Rank | Framework | Correctness | Latency | Consistency | Cost | LoC | CC |
|------|-----------|-------------|---------|-------------|------|-----|-----|
| 🥇 | **Claude Sdk** | 88.58% | 20.09s | 100% | $0.0380 | 72 | 3.0 |
| 🥈 | **Google Adk** | 85.42% | 15.43s | 75% | $0.00* | 158 | 2.0 |
| 🥉 | **Aws Strands** | 84.25% | 16.68s | 75% | $0.00* | 140 | 2.2 |
| 4. | **Crewai** | 82.00% | 16.99s | 75% | $0.0914 | 145 | 1.6 |

*Note: $0.00* indicates token tracking not available

---

## Per-Scenario Performance

### S1: Damaged Laptop Refund

| Framework | Correctness | Latency | Consistency |
|-----------|-------------|---------|-------------|
| Claude Sdk | 100.00% | 16.58s | 100% |
| Aws Strands | 100.00% | 12.31s | 100% |
| Google Adk | 100.00% | 14.08s | 100% |
| Crewai | 100.00% | 14.61s | 100% |

### S1b: Shipping Address Change

| Framework | Correctness | Latency | Consistency |
|-----------|-------------|---------|-------------|
| Claude Sdk | 100.00% | 17.82s | 100% |
| Aws Strands | 100.00% | 17.15s | 100% |
| Google Adk | 100.00% | 14.87s | 100% |
| Crewai | 78.00% | 17.00s | 0% |

### S1c: Billing Dispute Escalation

| Framework | Correctness | Latency | Consistency |
|-----------|-------------|---------|-------------|
| Claude Sdk | 75.00% | 18.57s | 100% |
| Aws Strands | 75.00% | 13.99s | 100% |
| Google Adk | 75.00% | 13.65s | 100% |
| Crewai | 75.00% | 17.86s | 100% |

### S2: The Frustrated Premium Customer (Complex)

| Framework | Correctness | Latency | Consistency |
|-----------|-------------|---------|-------------|
| Claude Sdk | 79.33% | 27.41s | 100% |
| Crewai | 75.00% | 18.50s | 100% |
| Google Adk | 66.67% | 19.13s | 0% |
| Aws Strands | 62.00% | 23.26s | 0% |

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
- **Average Latency**: 20.09s
- **Consistency**: 100%

**Performance by Complexity**:
- Simple scenarios (S1-S1c): 91.67%
- Complex scenarios (S2): 79.33%

### 🥈 Google Adk
- **Overall Correctness**: 85.42%
- **Average Latency**: 15.43s
- **Consistency**: 75%

**Performance by Complexity**:
- Simple scenarios (S1-S1c): 91.67%
- Complex scenarios (S2): 66.67%

### 🥉 Aws Strands
- **Overall Correctness**: 84.25%
- **Average Latency**: 16.68s
- **Consistency**: 75%

**Performance by Complexity**:
- Simple scenarios (S1-S1c): 91.67%
- Complex scenarios (S2): 62.00%

---

**Report Generated**: 2026-03-13 10:46:05
**Status**: ✅ Complete
**Total Frameworks**: 4
**Total Scenarios**: 4 (S1-S2)
**Total Runs**: 48
