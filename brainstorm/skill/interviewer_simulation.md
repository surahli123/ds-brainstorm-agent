# Interviewer Simulation Step

## When This Runs

After the 3-persona (or 4-persona) debate and synthesis are complete, run this step before
delivering the final output to the user.

## Purpose

Surface the 5 hardest questions a hiring panel would ask about this analysis. If any question
has no defensible answer, the corresponding claim must be killed or softened in the synthesis
before the user presents or submits the work.

This step is a final stress-test, not a post-mortem. Fix the analysis NOW, not after the panel.

---

## Step: Generate Interviewer Questions

### Input

Use the full synthesis output from the persona debate plus any anti_pattern matches from
the Claim Auditor (if activated).

### Process

1. **Identify the 5 most dangerous questions** the hiring panel would ask. Prioritize:
   - Questions that target any UNVERIFIED or CONTRADICTED claim from the Claim Auditor
   - Questions that probe treatment identification (outcome-based assignment = instant kill)
   - Questions that challenge causal claims without a valid counterfactual
   - Questions that expose metric-revenue disconnects (free-side vs. paying-side)
   - Questions that surface seasonality or confounding as alternative explanations
   - Questions about pre-registration of windows or hypotheses

2. **For each question, generate four fields:**
   - `question`: the exact wording the interviewer would use (first person, direct)
   - `best_answer`: the candidate's strongest 30-second response
   - `killer_followup`: the follow-up that could sink the candidate if unprepared
   - `prepared_response`: a prepared 2-3 sentence response to the killer follow-up

3. **Rank by likelihood** (1 = most likely to be asked first). Base ranking on:
   - How central the claim is to the analysis conclusion
   - How visible the weakness is (a contradicted headline number > a minor methodological gap)
   - How often this question type appears in DS interview feedback (treatment validity,
     counterfactuals, and metric definitions are the most common kill shots)

4. **Kill criterion:** If a question has NO defensible answer (i.e., the best_answer field
   would require fabricating data, asserting without evidence, or conceding the entire finding),
   mark it `"defensible": false`. The corresponding claim in the synthesis MUST be:
   - Killed (removed entirely), OR
   - Softened (reframed as a hypothesis or directional signal, not a causal finding)

   Do not deliver the final synthesis until all `"defensible": false` items are resolved.

---

## Output Format

```json
{
  "interviewer_simulation": {
    "analysis_summary": "one sentence describing the analysis being stress-tested",
    "questions": [
      {
        "rank": 1,
        "question": "exact interviewer phrasing",
        "best_answer": "candidate's strongest 30-second response",
        "killer_followup": "the follow-up that could sink the candidate",
        "prepared_response": "2-3 sentence prepared answer to the follow-up",
        "defensible": true,
        "targets_claim": "brief description of which analysis claim this probes"
      },
      {
        "rank": 2,
        "question": "...",
        "best_answer": "...",
        "killer_followup": "...",
        "prepared_response": "...",
        "defensible": false,
        "targets_claim": "...",
        "required_fix": "what must change in the synthesis before this is presentable"
      }
    ],
    "indefensible_count": 0,
    "synthesis_changes_required": ["list of changes to make to synthesis before delivering"]
  }
}
```

---

## Integration Note

This step runs AFTER the persona debate and BEFORE delivering the final synthesis to the user.
If `synthesis_changes_required` is non-empty, apply the changes to the synthesis output first,
then deliver both the updated synthesis and the interviewer simulation to the user.

The user receives:
1. Updated synthesis (with indefensible claims killed or softened)
2. Interviewer simulation (so they can prepare)
