# AI Agent Security — Multi-Step Tool Attacks (Kaggle)

**Top-tier finish (4th of 4,186 competitors) in my first-ever Kaggle competition**,
a $50,000 red-teaming challenge on multi-step tool attacks against AI agents. Team
"no shake thanks :)".

## The short version

Attackers were scored on how reliably they could drive a tool-using LLM agent into
unsafe multi-step behavior. I entered with no formal machine-learning background and
one self-imposed rule: **I would not hand-write the solution code** — every script,
harness, and payload would be produced by AI agents I directed, reviewed, and
orchestrated. The point was to prove that disciplined orchestration of AI, plus real
engineering judgment, could compete with trained ML practitioners. It did.

## What made the result possible (the engineering)

- **Reverse-engineered the grader.** I decoded the scoring formula out of the
  competition SDK, which turned a black-box leaderboard into a function I could
  optimize against directly.
- **Built an offline validation harness.** Instead of burning scarce daily
  leaderboard submissions to learn, I reproduced the grader locally — parse a
  payload, score it, iterate — so mistakes were free and fast. This was the single
  biggest lever.
- **Attack-family analysis.** An offline dashboard tracked score progression per
  payload family and exposed the plateaus where an approach topped out, telling me
  when to switch strategy rather than grind.
- **Multi-agent ideation ("Council").** A desktop tool that seated several AI
  advisors around one problem and let them argue to convergence produced payload
  directions I would not have reached alone.

## Why it matters to an employer

- A measurable, competitive result in **AI security / LLM red-teaming** — one of the
  most active problems in the field right now.
- Demonstrates the modern skill that actually ships product: **orchestrating AI
  systems** to do real work, with the judgment to reverse-engineer the objective,
  build the right tooling, and know when to change course.
- Shows I can go from zero domain knowledge to a top-0.1% result by engineering the
  problem instead of grinding it.

## In this folder

- `AISEC_WHITEPAPER_REVISED.md` — the full evidence-backed write-up (method, harness,
  attack families, and lessons), formatted as a white paper.

Handle: **wraith53**.
