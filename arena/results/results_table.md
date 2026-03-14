# Arena Benchmark Results

Run date: 2026-03-13

## Summary Table

| Framework | LoC | CC | Avg Tokens (In/Out) | Avg Step Eff | Avg Latency (s) | Avg Correct | Avg Cost ($) | Avg pass³ |
|-----------|-----|----|--------------------|--------------|-----------------|-------------|--------------|-----------|
| claude_sdk | 118 | 3.2 | 18142/1828 | 0.67 | 35.06 | 0.87 | 0.0835 | 1.00 |
| langchain | 136 | 2.4 | 6517/704 | 0.63 | 15.68 | 0.76 | 0.0301 | 0.67 |
| langgraph | 136 | 2.4 | 6517/760 | 0.63 | 15.92 | 0.76 | 0.0310 | 0.67 |
| aws_strands | 141 | 2.4 | 7469/758 | 0.67 | 16.85 | 0.84 | 0.0338 | 1.00 |
| crewai | 146 | 1.6 | 6134/925 | 0.63 | 18.10 | 0.84 | 0.0323 | 1.00 |
| google_adk | 162 | 2.5 | 6803/798 | 0.67 | 17.18 | 0.78 | 0.0324 | 0.67 |

## Detailed Results by Scenario


### claude_sdk


**T1:**
- Median latency: 23.32s
- Median tokens: 12561 in / 1111 out
- Median cost: $0.0543
- Median step efficiency: 1.0
- Consistency (pass³): 1.0
- Per-run correctness: [1.0, 1.0, 1.0]

**T4:**
- Median latency: 44.41s
- Median tokens: 21744 in / 2288 out
- Median cost: $0.0992
- Median step efficiency: 0.5
- Consistency (pass³): 1.0
- Per-run correctness: [0.75, 0.88, 0.88]

**T5:**
- Median latency: 37.45s
- Median tokens: 20121 in / 2085 out
- Median cost: $0.0971
- Median step efficiency: 0.5
- Consistency (pass³): 1.0
- Per-run correctness: [0.77, 0.77, 0.77]

### langchain


**T1:**
- Median latency: 11.85s
- Median tokens: 5082 in / 424 out
- Median cost: $0.0216
- Median step efficiency: 1.0
- Consistency (pass³): 1.0
- Per-run correctness: [1.0, 1.0, 1.0]

**T4:**
- Median latency: 17.66s
- Median tokens: 5668 in / 744 out
- Median cost: $0.0282
- Median step efficiency: 0.4
- Consistency (pass³): 0.0
- Per-run correctness: [0.5, 0.5, 0.5]

**T5:**
- Median latency: 17.53s
- Median tokens: 8801 in / 944 out
- Median cost: $0.0406
- Median step efficiency: 0.5
- Consistency (pass³): 1.0
- Per-run correctness: [0.77, 0.77, 0.77]

### langgraph


**T1:**
- Median latency: 10.88s
- Median tokens: 5082 in / 424 out
- Median cost: $0.0216
- Median step efficiency: 1.0
- Consistency (pass³): 1.0
- Per-run correctness: [1.0, 1.0, 1.0]

**T4:**
- Median latency: 16.95s
- Median tokens: 5668 in / 744 out
- Median cost: $0.0282
- Median step efficiency: 0.4
- Consistency (pass³): 0.0
- Per-run correctness: [0.5, 0.5, 0.5]

**T5:**
- Median latency: 19.94s
- Median tokens: 8801 in / 1114 out
- Median cost: $0.0431
- Median step efficiency: 0.5
- Consistency (pass³): 1.0
- Per-run correctness: [0.77, 0.77, 0.77]

### aws_strands


**T1:**
- Median latency: 10.78s
- Median tokens: 5235 in / 411 out
- Median cost: $0.0219
- Median step efficiency: 1.0
- Consistency (pass³): 1.0
- Per-run correctness: [1.0, 1.0, 1.0]

**T4:**
- Median latency: 19.17s
- Median tokens: 8175 in / 858 out
- Median cost: $0.0374
- Median step efficiency: 0.5
- Consistency (pass³): 1.0
- Per-run correctness: [0.75, 0.75, 0.75]

**T5:**
- Median latency: 20.6s
- Median tokens: 8997 in / 1005 out
- Median cost: $0.0421
- Median step efficiency: 0.5
- Consistency (pass³): 1.0
- Per-run correctness: [0.77, 0.77, 0.77]

### crewai


**T1:**
- Median latency: 12.29s
- Median tokens: 5634 in / 506 out
- Median cost: $0.0245
- Median step efficiency: 1.0
- Consistency (pass³): 1.0
- Per-run correctness: [1.0, 1.0, 1.0]

**T4:**
- Median latency: 22.46s
- Median tokens: 6068 in / 1070 out
- Median cost: $0.0343
- Median step efficiency: 0.4
- Consistency (pass³): 1.0
- Per-run correctness: [0.75, 0.75, 0.75]

**T5:**
- Median latency: 19.55s
- Median tokens: 6701 in / 1199 out
- Median cost: $0.0381
- Median step efficiency: 0.5
- Consistency (pass³): 1.0
- Per-run correctness: [0.77, 0.77, 0.77]

### google_adk


**T1:**
- Median latency: 12.18s
- Median tokens: 5216 in / 442 out
- Median cost: $0.0223
- Median step efficiency: 1.0
- Consistency (pass³): 1.0
- Per-run correctness: [1.0, 1.0, 1.0]

**T4:**
- Median latency: 19.99s
- Median tokens: 5984 in / 945 out
- Median cost: $0.0322
- Median step efficiency: 0.5
- Consistency (pass³): 0.0
- Per-run correctness: [0.5, 0.62, 0.62]

**T5:**
- Median latency: 19.36s
- Median tokens: 9210 in / 1007 out
- Median cost: $0.0427
- Median step efficiency: 0.5
- Consistency (pass³): 1.0
- Per-run correctness: [0.77, 0.77, 0.77]