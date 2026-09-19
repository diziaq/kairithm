# Sessions

One directory per interview, named `<date>_<time>_<candidate>_<role>`. Each holds:

- `session.json` — the full machine-readable state, written atomically as you work;
- `summary.md` — one page about the candidate, written when the interview is finished;
- `scorecard.md` — the full record, with the evidence per question.

`summary.md` is the one to paste into a hiring thread first. It carries the range, the strong and
weak areas and nothing about how the interview was run. `scorecard.md` carries everything.

The tool creates this directory if it is missing. Commit the results you want to keep.
