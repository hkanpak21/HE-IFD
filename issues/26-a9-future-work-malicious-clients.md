# 26. A9 future-work paragraph on malicious / colluding clients

Status: ready-for-agent
Label: AFK
Priority: P3 (text-only; no dependencies)
Action-plan: A9
PRD-section: §2.6 (out-of-scope adversaries)

## Parent

Action plan A9 (lines 392–399). Resolves [AE-4] and [R2-Q4].

## What to build

One discussion paragraph (half a page) in §future-work that:

1. Names the threats explicitly:
   - Encrypted-feature poisoning (clients craft adversarial logit ciphertexts).
   - Model poisoning under encryption (clients submit ciphertexts that bias the aggregate).
   - Robust aggregation compatible with HE (where prior plaintext-aggregation defences do not directly port).
2. Cites Viand SoK 2023 (`viand2023verifiable`, already in `references.bib` per CHANGES.md §5.2) and one recent vCKKS reference as the natural extension toward verifiable HE.
3. Is explicit about the **out-of-scope** status — this is not a defence claim, it is an acknowledgement that bounds the work.
4. The cover letter [reports/cover_letter_draft.md](../reports/cover_letter_draft.md) §6 (or wherever it acknowledges out-of-scope concerns) should add a one-liner pointing here.

Voice: austere theoretical register (memory `feedback-paper-voice`).

## Acceptance criteria

- [ ] One paragraph (≈ half a page) added to `conclusion.tex` §future-work (or `discussion.tex` if that file exists post-issue-16).
- [ ] Three threats named explicitly per above.
- [ ] `viand2023verifiable` cited.
- [ ] At least one concrete vCKKS reference cited (Atapoor et al. 2024, Knabenhans et al. vCKKS, or equivalent; add to `references.bib` if not present).
- [ ] Out-of-scope status stated unambiguously.
- [ ] `FL_TDSC/CHANGES.md` updated.

## Blocked by

None — can start immediately.

## References

- Action plan A9 (lines 392–399).
- PRD §2.6 (lines 76–80).
- `references.bib`: `viand2023verifiable`.

## Comments

(none yet)
