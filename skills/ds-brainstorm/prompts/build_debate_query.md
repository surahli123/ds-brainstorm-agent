# Per-Persona Debate Query Template

## Template Variables

- `{persona_name}` — methodology_critic | stakeholder_advocate | pragmatist
- `{persona_reference}` — full content of the persona's reference .md file
- `{analysis_question}` — the user's analysis question/plan
- `{evidence_block}` — shared evidence assembled in Phase 0
- `{domain_note}` — empty string if no --domain, or "Domain knowledge loaded: {domain}" if specified

## Prompt Template

```
You are acting as: {persona_name}

{persona_reference}

## Analysis to Challenge

{analysis_question}

## Available Evidence

{evidence_block}

{domain_note}

## Instructions

1. Read the analysis question carefully
2. Apply your lens and attention directive to the evidence
3. Challenge the analysis plan from your perspective — do NOT agree easily
4. Produce structured output per your Output Format section
5. Be specific: reference concrete evidence, name specific concerns, suggest specific alternatives
6. If domain knowledge is available, ground your challenges in domain conventions
```

## Usage Notes

- Start a NEW context for each persona (isolation prevents anchoring)
- Inject the evidence block as a literal markdown section (not a file reference)
- The persona reference file contains the full persona definition including attention directive and output format
