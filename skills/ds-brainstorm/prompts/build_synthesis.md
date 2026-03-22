# Cross-Persona Challenge Synthesis Template

## Template Variables

- `{analysis_question}` — the user's original analysis question
- `{critic_output}` — Methodology Critic's structured response
- `{advocate_output}` — Stakeholder Advocate's structured response
- `{pragmatist_output}` — Pragmatist's structured response

## Prompt Template

```
You have 3 independent assessments of the same analysis plan from different perspectives.
Your job is to synthesize them into a structured challenge for the user — NOT a consensus summary.

## Analysis Question
{analysis_question}

## Methodology Critic Assessment
{critic_output}

## Stakeholder Advocate Assessment
{advocate_output}

## Pragmatist Assessment
{pragmatist_output}

## Synthesis Instructions

1. **Agreements:** Where do all 3 perspectives align? These are strong signals.
   List each as a clear statement.

2. **Tensions:** Where do perspectives DISAGREE? Stage each as an explicit exchange:
   "Methodology Critic says: [X]. But Pragmatist counters: [Y]."
   Do NOT resolve tensions — present them as debates for the user to weigh in on.

3. **Key Question:** What is the SINGLE most important tension the user needs to resolve
   before proceeding? Frame it as a direct question to the user.

4. **Priority:** Which perspective's concerns are most urgent given the user's context?

## Output Format

Present the synthesis as:
- 2-3 agreements (bullet list)
- 2-3 tensions (staged as back-and-forth exchanges)
- 1 key question (the most important thing to resolve)
- Then ask the user to respond
```
