# AI Agent Token Efficiency Guide

A comprehensive guide for optimizing token usage in AI agent interactions.

---

## Core Principles

### 1. Less is More
- Shorter, well-scoped inputs yield sharper responses
- Bloated prompts confuse the model, increase latency/cost, and raise hallucination risk
- Clear instructions + relevant examples > stuffing full context

### 2. Smart Context Injection
- Only include information directly relevant to the current task
- Remove redundant data before sending to the model
- Use semantic search to find relevant context vs dumping everything

---

## Prompt Engineering Strategies

### Concise Prompts (30-50% savings)
```
BAD:  "I would like you to please help me by writing a function that
       takes a number as input and returns whether it is prime"

GOOD: "Write isPrime(n) function - return true if prime, false otherwise"
```

### Structured Requests
```
BAD:  Long paragraph explaining what you want

GOOD:
- Task: [one line]
- Input: [specifics]
- Output: [format]
- Constraints: [if any]
```

### Reference by Path, Not Content
```
BAD:  "Here's the entire file content: [500 lines]..."

GOOD: "In src/auth.py, fix the token expiry on line 48"
```

---

## For AI Agents: Operational Guidelines

### When Reading Files
1. Read only files you need
2. Use `offset` and `limit` for large files
3. Don't re-read files already in context

### When Searching
1. Use specific patterns: `class UserAuth` vs `user`
2. Limit search scope: specify directory/file type
3. Use `head_limit` on grep results

### When Responding
1. Be concise - no filler words
2. Use bullet points over paragraphs
3. Code > explanation when showing changes
4. One summary line per completed task

### When Planning
1. Break into small, focused tasks
2. Execute sequentially - don't load all context upfront
3. Complete and forget - don't carry unnecessary state

---

## Tool Usage Optimization

### Parallel vs Sequential
```
PARALLEL (efficient): Independent operations
- Read file A, Read file B, Search for X

SEQUENTIAL (required): Dependent operations
- Read file → Edit file → Build → Test
```

### Batch Operations
```
BAD:  5 separate commits for 5 related changes

GOOD: 1 commit with all related changes
```

### Avoid Redundant Reads
```
BAD:  Read file, make edit, read file again to verify

GOOD: Read file, make edit, trust the tool output
```

---

## Context Management Techniques

### 1. Summarization
- Summarize long outputs before storing
- Keep only essential details from API responses
- Compress error logs to key information

### 2. Chunking
- Process large files in sections
- Handle lists item-by-item
- Break complex tasks into phases

### 3. Forgetting
- Don't reference old, irrelevant context
- Each task should be self-contained
- Avoid "as I mentioned earlier" patterns

---

## Communication Efficiency

### Status Updates
```
BAD:  "I have successfully completed the task of updating the
       authentication module. The changes include..."

GOOD: "Done. Auth module updated - token expiry now 24h."
```

### Error Reporting
```
BAD:  Full stack trace + explanation + suggestions

GOOD: "Error: missing import on line 5. Fixed."
```

### Confirmations
```
BAD:  "I understand you want me to... Let me proceed with..."

GOOD: [Just do the task]
```

---

## Model Tiering Strategy

| Task Type | Model Choice |
|-----------|--------------|
| Simple classification | Fast/cheap (haiku) |
| Code generation | Standard (sonnet) |
| Complex reasoning | Premium (opus) |
| Quick searches | Fast (haiku) |

---

## Metrics to Track

1. **Tokens per task** - Lower is better
2. **Tool calls per task** - Minimize redundant calls
3. **Context reuse** - Don't re-fetch same data
4. **Response length** - Concise but complete

---

## Quick Reference Checklist

Before each interaction:
- [ ] Is all this context necessary?
- [ ] Can I reference instead of include?
- [ ] Am I using the right model tier?
- [ ] Can operations run in parallel?

During execution:
- [ ] Read only what's needed
- [ ] Search with specific patterns
- [ ] Batch related operations
- [ ] Skip verbose confirmations

After completion:
- [ ] One-line summary sufficient?
- [ ] Can context be discarded?
- [ ] Is follow-up truly needed?

---

## Sources

- [JetBrains Research: Efficient Context Management](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)
- [Deepchecks: 5 Approaches to Solve LLM Token Limits](https://www.deepchecks.com/5-approaches-to-solve-llm-token-limits/)
- [Agenta: Top Techniques to Manage Context Length](https://agenta.ai/blog/top-6-techniques-to-manage-context-length-in-llms)
- [Medium: Token Optimization for AI Agents](https://medium.com/elementor-engineers/optimizing-token-usage-in-agent-based-assistants-ffd1822ece9c)
- [Speakeasy: Reducing MCP Token Usage](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2)
- [SparkCo: Optimizing Token Usage 2025](https://sparkco.ai/blog/optimizing-token-usage-for-ai-efficiency-in-2025/)
- [K2View: MCP Strategies for Token Efficiency](https://www.k2view.com/blog/mcp-strategies-for-grounded-prompts-and-token-efficient-llm-context/)
