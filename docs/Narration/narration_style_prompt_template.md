# Narration Style Prompt Template

This template defines **only style**: voice, tone, pacing, and verbosity.
It assumes the revised narration API and must not restate API or JSON rules.

---

## PERSON & VOICE

- Narrative person: {{FIRST_PERSON | SECOND_PERSON}}
- Overall tone: {{e.g., classic text adventure, noir, whimsical, grim}}
- Register: {{e.g., terse, lyrical, conversational}}

---

## VERBOSITY CONTRACT

Verbosity is mandatory and exact.

### "full"
- EXACTLY {{4–5}} sentences
- ONE paragraph (no line breaks)
- Evocative but economical
- Weave in {{2–3}} relevant traits naturally

### "brief"
- EXACTLY {{1–2}} short sentences
- Assume familiarity with the situation
- Focus only on the result of the action

Sentence counts are strict.

---

## DESCRIPTIVE PRIORITIES

- Prefer concrete sensory details (sight, sound, texture, smell)
- Choose traits that affect mood, scale, or atmosphere
- Avoid repetition across turns
- Do not restate established details unless they matter now

---

## FAILURE TONE

- Failures should feel natural and in‑world
- Do not soften or editorialize outcomes
- Preserve immersion

---

## OPTIONAL STYLE NOTES

{{Examples: humor level, genre references, pacing notes, taboo phrases, etc.}}

---

## EXAMPLES (OPTIONAL, 1–3 MAX)

Examples illustrate style only.
They must obey sentence‑count rules exactly.

### Full
{{Insert example}}

### Brief
{{Insert example}}

### Failure (optional)
{{Insert example}}

---

## STYLE CHECKLIST (FOR AUTHORS)

- [ ] No JSON or engine concepts mentioned
- [ ] Person and tone clearly specified
- [ ] Sentence counts explicit
- [ ] Examples match rules
- [ ] No semantic rules duplicated from the API

