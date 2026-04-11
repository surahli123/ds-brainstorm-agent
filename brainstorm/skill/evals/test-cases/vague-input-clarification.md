# Eval: Vague Input Triggers Clarification

## Test Input

"I want to analyze the impact of our new model on performance"

## Expected Behavior

1. Step 0.1.5 fires (input lacks specific metric, comparison, and scope)
2. F/D/Q classification produced:
   - F: A new model exists
   - D: User wants to measure its effect
   - Q: Which metric, which aspect of performance, compared to what
3. Vague words detected: "impact" (which metric?), "performance" (latency? quality?)
4. At most 1 Socratic question asked
5. Clarified statement produced with specific metric and scope

## Anti-Patterns (should NOT happen)

- Clarification skipped (input is clearly vague)
- More than 2 dialogue turns consumed
- Framework names mentioned ("Wittgenstein", "Polanyi")
- All 3 Polanyi strategies offered at once
- Generic F/D/Q shown to precise input (skip condition test):
  Input: "Measure NDCG@10 delta between model A and B on navigational queries over 2 weeks"
  → Should skip clarification entirely

## Edge Case: Multi-Topic Discovery

Input: "I want to analyze the impact of the new ranking model and also look into
why our query classification accuracy dropped last week"

Expected: F/D/Q reveals 2 independent analyses → loops back to scope check →
asks user which to brainstorm first
