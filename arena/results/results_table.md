# Arena Benchmark Results

Run date: 2026-03-13

## Summary Table

| Framework | LoC | CC | Avg Tokens (In/Out) | Avg Step Eff | Avg Latency (s) | Avg Correct | Avg Cost ($) | Avg pass³ |
|-----------|-----|----|--------------------|--------------|-----------------|-------------|--------------|-----------|
| claude_sdk | 118 | 3.2 | 15579/2020 | 0.50 | 34.02 | 0.26 | 0.0770 | 0.00 |
| langchain | 136 | 2.4 | 8801/970 | 0.50 | 17.96 | 0.26 | 0.0410 | 0.00 |
| langgraph | 136 | 2.4 | 8801/944 | 0.50 | 18.59 | 0.26 | 0.0406 | 0.00 |
| aws_strands | 141 | 2.4 | 8997/1005 | 0.50 | 22.53 | 0.26 | 0.0421 | 0.00 |
| crewai | 146 | 1.6 | 6701/1199 | 0.50 | 19.98 | 0.26 | 0.0381 | 0.00 |
| google_adk | 162 | 2.5 | 7166/1048 | 0.50 | 19.80 | 0.26 | 0.0372 | 0.00 |

## Detailed Results by Scenario


### claude_sdk


**S3:**
- Median latency: 34.02s
- Median tokens: 15579 in / 2020 out
- Median cost: $0.077
- Median step efficiency: 0.5
- Consistency (pass³): 0.0
- Per-run correctness: [0.77, 0.0, 0.0]

### langchain


**S3:**
- Median latency: 17.96s
- Median tokens: 8801 in / 970 out
- Median cost: $0.041
- Median step efficiency: 0.5
- Consistency (pass³): 0.0
- Per-run correctness: [0.77, 0.0, 0.0]

### langgraph


**S3:**
- Median latency: 18.59s
- Median tokens: 8801 in / 944 out
- Median cost: $0.0406
- Median step efficiency: 0.5
- Consistency (pass³): 0.0
- Per-run correctness: [0.77, 0.0, 0.0]

### aws_strands


**S3:**
- Median latency: 22.53s
- Median tokens: 8997 in / 1005 out
- Median cost: $0.0421
- Median step efficiency: 0.5
- Consistency (pass³): 0.0
- Per-run correctness: [0.77, 0.0, 0.0]

### crewai


**S3:**
- Median latency: 19.98s
- Median tokens: 6701 in / 1199 out
- Median cost: $0.0381
- Median step efficiency: 0.5
- Consistency (pass³): 0.0
- Per-run correctness: [0.77, 0.0, 0.0]

### google_adk


**S3:**
- Median latency: 19.8s
- Median tokens: 7166 in / 1048 out
- Median cost: $0.0372
- Median step efficiency: 0.5
- Consistency (pass³): 0.0
- Per-run correctness: [0.77, 0.0, 0.0]