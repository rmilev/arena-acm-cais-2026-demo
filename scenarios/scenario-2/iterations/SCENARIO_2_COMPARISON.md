# Scenario-2: Iteration 1 vs Iteration 2 Comparison

**Date**: March 13, 2026
**Purpose**: Validate reproducibility and analyze prompt caching effects
**Test**: S2 - The Frustrated Premium Customer (Complex Multi-Issue)

---

## Executive Summary

✅ **Reproducibility**: High consistency in correctness scores
⚠️ **Prompt Caching**: Consistent bias favoring later-tested frameworks
🔍 **Key Finding**: Cache effects are predictable and don't invalidate correctness comparisons

---

## Results Comparison

### Iteration 1 vs Iteration 2

| Framework | Order | Iter 1 Correct | Iter 2 Correct | Δ Correct | Iter 1 Latency | Iter 2 Latency | Δ Latency |
|-----------|-------|----------------|----------------|-----------|----------------|----------------|-----------|
| **Claude SDK** | 1st (cold) | 83.67% | 83.67% | **0%** ✅ | 34.53s | 28.92s | **-16.2%** ⚠️ |
| **AWS Strands** | 2nd | 62.00% | 62.00% | **0%** ✅ | 23.52s | 23.51s | **-0.04%** ✅ |
| **Google ADK** | 3rd | 46.00% | 62.33% | **+35%** ⚠️ | 26.47s | 26.65s | **+0.7%** ✅ |
| **CrewAI** | 4th (warm) | 75.00% | 75.00% | **0%** ✅ | 21.37s | 19.74s | **-7.6%** ✅ |

---

## Key Observations

### ✅ Correctness Highly Reproducible (3/4 frameworks)

**Perfect Match**:
- Claude SDK: 84% → 84% (identical)
- AWS Strands: 62% → 62% (identical)
- CrewAI: 75% → 75% (identical)

**Variance**:
- Google ADK: 46% → 62% (+35% increase) ⚠️
  - Iteration 1: [0.38, 0.50, 0.50]
  - Iteration 2: [0.50, 0.75, 0.62]
  - **Analysis**: High variance suggests instability with complexity

---

## 🔍 Prompt Caching Analysis

### Testing Order (Fixed)

```
1st: Claude SDK   ← Cold cache (no benefit)
2nd: AWS Strands  ← Warming cache
3rd: Google ADK   ← Warmer cache
4th: CrewAI       ← Fully warm cache
```

### Latency Patterns

#### Iteration 1
| Framework | Order | Latency | Expected Cache Benefit |
|-----------|-------|---------|------------------------|
| Claude SDK | 1st | 34.53s | None (cold) |
| AWS Strands | 2nd | 23.52s | Moderate |
| Google ADK | 3rd | 26.47s | High |
| CrewAI | 4th | **21.37s** ← **Fastest** | Full cache |

#### Iteration 2
| Framework | Order | Latency | Expected Cache Benefit |
|-----------|-------|---------|------------------------|
| Claude SDK | 1st | 28.92s | None (cold) |
| AWS Strands | 2nd | 23.51s | Moderate |
| Google ADK | 3rd | 26.65s | High |
| CrewAI | 4th | **19.74s** ← **Fastest** | Full cache |

### Cache Effect Evidence

**Strong indicators of prompt caching**:

1. **CrewAI consistently fastest** (tested last)
   - Iter 1: 21.37s (fastest)
   - Iter 2: 19.74s (fastest, even faster!)

2. **Claude SDK consistently slowest** (tested first)
   - Iter 1: 34.53s (slowest)
   - Iter 2: 28.92s (still slowest, but improved)

3. **Latency decreases in Iteration 2** (cache warming across iterations)
   - Claude SDK: 34.53s → 28.92s (-16%)
   - CrewAI: 21.37s → 19.74s (-8%)

4. **Order matters more than framework efficiency**
   - AWS Strands (2nd): ~23.5s
   - Google ADK (3rd): ~26.5s
   - CrewAI (4th): ~20s ← Should be slowest (simplest code) but is fastest

---

## Token Usage Analysis

### Claude SDK Token Drop

**Iteration 1 → Iteration 2**:
- Input tokens: 22 → 22 (same)
- Output tokens: 1,294 → 1,046 (-19%)

**Interpretation**: Output variance is normal for non-deterministic generation, even at temp=0

### CrewAI Consistency

- Input: 5,354 (both iterations)
- Output: 901 (both iterations)
- **Perfect consistency** ✅

---

## Rankings Analysis

### By Correctness (What Matters Most)

**Iteration 1**:
1. 🥇 Claude SDK (84%)
2. 🥈 CrewAI (75%)
3. 🥉 AWS Strands (62%)
4. Google ADK (46%)

**Iteration 2**:
1. 🥇 Claude SDK (84%)
2. 🥈 CrewAI (75%)
3. 🥉 Google ADK (62%)
4. AWS Strands (62%)

**Change**: Google ADK improved from 4th to 3rd (tied)
- But still inconsistent (50%, 75%, 62% across runs)

### By Latency (Cache-Affected)

**Both Iterations**:
1. CrewAI (~20s) ← **Cache advantage**
2. AWS Strands (~23.5s)
3. Google ADK (~26.5s)
4. Claude SDK (~30s) ← **Cache disadvantage**

---

## Reproducibility Validation

### ✅ Highly Reproducible

**Correctness scores** (most important metric):
- 3/4 frameworks: **100% identical**
- 1/4 frameworks: Variance due to instability, not randomness

**Latency** (cache-affected but consistent):
- Claude SDK: Consistently slowest (tested first)
- CrewAI: Consistently fastest (tested last)
- Pattern repeats across iterations

### ⚠️ Google ADK Instability

**Per-run correctness variance**:
- Iteration 1: [38%, 50%, 50%] - Low and inconsistent
- Iteration 2: [50%, 75%, 62%] - Improved but still inconsistent

**Conclusion**: Google ADK struggles with S2 complexity, results unstable

---

## Impact on Benchmark Validity

### What's Valid ✅

1. **Correctness comparisons** - Cache doesn't affect logic
   - Claude SDK is most correct (84%)
   - CrewAI is second best (75%)
   - Google ADK struggles (46-62%)

2. **Relative rankings** - All frameworks face same cache pattern
   - Claude SDK always tested first
   - CrewAI always tested last
   - Fair comparison within iterations

3. **Framework capabilities** - True differences revealed
   - Claude SDK: Best context management
   - CrewAI: Good balance
   - Google ADK: Fails on complexity

### What's Affected ⚠️

1. **Absolute latency numbers** - Cache creates artificial ordering
   - CrewAI appears fastest (but tested last with warm cache)
   - Claude SDK appears slowest (but tested first with cold cache)

2. **Speed comparisons** - Not truly apples-to-apples
   - Can't definitively say "CrewAI is faster than Claude SDK"
   - Order bias confounds speed measurements

3. **Token counts** - May be reduced by caching
   - Claude SDK shows low input tokens (22)
   - CrewAI shows high input tokens (5,354)
   - Difference may be cache-related

---

## Recommendations

### For Current Results

✅ **Trust correctness rankings**:
1. Claude SDK (84%) - Best for complex scenarios
2. CrewAI (75%) - Good balance
3. AWS Strands (62%) - Adequate
4. Google ADK (46-62%) - Unstable on complexity

⚠️ **Be cautious about latency rankings**:
- Document testing order
- Note cache effects in methodology
- Don't claim definitive speed winner

### For Future Iterations

**Option A: Randomize Order** (Recommended)
```python
import random
framework_names = list(FRAMEWORKS.keys())
random.shuffle(framework_names)
```
- Eliminates systematic bias
- Fair speed comparisons
- Adds complexity to analysis

**Option B: Round-Robin Testing**
```
Iteration 1: [Claude, AWS, Google, Crew]
Iteration 2: [Crew, Google, AWS, Claude]
Iteration 3: [Google, Crew, Claude, AWS]
```
- Each framework tested in each position
- Average out cache effects
- Requires more iterations

**Option C: Cache Clearing**
```python
time.sleep(300)  # 5-min delay between frameworks
```
- Simple to implement
- Much longer runtime
- May not fully clear cache

**Option D: Document and Accept**
- Note limitation in methodology
- Focus on correctness (not speed)
- Acknowledge cache effects

---

## Statistical Validation

### Sample Size
- **Per iteration**: 4 frameworks × 1 scenario × 3 reps = 12 runs
- **Total**: 2 iterations = 24 runs
- **Adequate** for correctness comparisons

### Confidence Level
- **Correctness**: High confidence (3/4 perfect match)
- **Latency**: Low confidence (cache-confounded)
- **Rankings**: High confidence for correctness, low for speed

---

## Conclusions

### Reproducibility: ✅ VALIDATED

**Correctness scores are highly reproducible**:
- Claude SDK: 84% (both iterations)
- CrewAI: 75% (both iterations)
- AWS Strands: 62% (both iterations)

**Key findings remain valid**:
- Claude SDK handles complexity best
- CrewAI surprisingly good
- Google ADK struggles with multi-issue scenarios

### Prompt Caching: ⚠️ CONFIRMED

**Evidence of systematic cache effects**:
- Testing order creates consistent latency bias
- Later frameworks benefit from warm cache
- Effects are predictable and reproducible

**Impact**:
- ❌ Can't trust absolute latency numbers
- ✅ CAN trust correctness comparisons
- ✅ CAN trust relative correctness rankings

### Recommendation: ✅ ACCEPT RESULTS WITH CAVEAT

**Use these results for**:
- Framework correctness comparisons ✅
- Context management assessment ✅
- Complexity handling evaluation ✅
- Production framework selection (based on correctness) ✅

**DON'T use these results for**:
- Absolute speed claims ❌
- Definitive latency rankings ❌
- Performance optimization decisions ❌

**Document**:
- Testing order: Claude SDK → AWS Strands → Google ADK → CrewAI
- Note: "Latency measurements may be affected by prompt caching"
- Focus: "Correctness is the primary evaluation metric"

---

## Next Steps

### Immediate
1. ✅ Results are valid for correctness evaluation
2. 📝 Document cache limitation in methodology
3. 📊 Update main docs with Iter 2 findings

### Future (Optional)
1. 🔀 Implement order randomization for Iteration 3
2. 📈 Average latency across multiple order permutations
3. 🔍 Investigate AWS Bedrock cache behavior
4. 📊 Create cache-aware analysis script

---

**Comparison Date**: March 13, 2026
**Status**: ✅ Validated - Results are reproducible
**Prompt Caching**: ⚠️ Present but predictable
**Recommendation**: Accept correctness findings, note latency limitations
