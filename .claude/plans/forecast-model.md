# Forecast model plan

**Goal:** A public Python repo that produces a frozen, git-tagged forecast for
all 435 House races and every 2026 Senate race before Election Day. It uses a
"classic + light factor" model: Senate poll average + lean prior; House district
lean + generic ballot + incumbency; a fat-tailed national shock + one
sub-national factor + race noise. A quick 2022 backtest sanity-checks it. Done
means a frozen handoff artifact (per-race parameters + simulation draws + race
metadata) exists under a git tag. The election-night plan can load it to
re-simulate with called races locked in, and it reports P(D House), P(D Senate),
seat distributions, and per-race P(win).

**How to use this doc (multi-session):** work one unit at a time. Each step has
a checkbox and an acceptance check; when it passes, tick it and add a dated line
to the Progress log — the log is the _only_ home for narrative. At the start of
a session, read the Current-state snapshot + the first unchecked step and resume
there. Keep every section within its length cap (noted below); a `prettier` hook
auto-formats this file on save, so don't hand-align tables or fuss over
wrapping.

## Why this exists (problems to fix)

1. No forecast exists. The repo is blank apart from `CLAUDE.md`.
2. Most House districts are unpolled, so they need a fundamentals prior on the
   2026 maps (about 40% of seats are on new lines).
3. No source has been picked yet for 2026 nominees, incumbency, open seats, or
   uncontested races (B9).
4. Control odds need correct seat accounting: Senate holdovers, independents'
   caucus, VP tiebreak, House 218 threshold, and special rules (GA, ME/AK RCV,
   CA/WA top-two, LA).
5. The election-night plan needs a stable handoff artifact, and needs its schema
   early so the two plans can progress in parallel.
6. Error variances are guesses until checked against a real past cycle (2022).
7. The forecast must be provably pre-election (frozen and tagged before results
   exist).

## Decisions log

- **D1 — Model tier.** Classic + light factor; no house effects, LV adjustment,
  or full factor model. **RESOLVED (2026-10-24) → classic + light factor**
  because the full reference approach doesn't fit about 15 hours.
- **D2 — Authoring split.** Claude writes the code; the user reviews it.
  **RESOLVED (2026-10-24) → Claude writes** because of the 10-day deadline.
- **D3 — Stack.** **RESOLVED (2026-10-24) → Python 3.12, uv, pandas/numpy,
  pytest, ruff**, matching the user's tooling.
- **D4 — Poll source.** **RESOLVED (2026-10-24) → FiftyPlusOne**. Its ToS
  decides whether raw files get committed or gitignored (step 1.1).
- **D5 — Validation.** **RESOLVED (2026-10-24) → quick 2022 House backtest**;
  second to cut after the dashboard map.
- **D6 — Freeze.** Around the evening of 2026-11-02, marked with a git tag.
  **PARTLY RESOLVED (2026-10-24)**; exact time and manifest open (CLAUDE.md A4),
  decide at 6.3.
- **D7 — Handoff format.** Proposal: per-race parameters + national/factor
  parameters + draws. Filtering draws alone collapses after about 15 calls (see
  Pinned). **OPEN → decide at 0.4.**
- **D8 — Light factor.** Region (Census divisions) vs. lean bucket vs. a
  demographic proxy. **OPEN → decide at 4.1.**
- **D9 — Code license.** MIT vs. Apache-2.0 vs. other (CLAUDE.md E12).
  **RESOLVED (2026-10-24) → MIT** because it's the simplest choice for a public
  portfolio repo; data terms are tracked per source.
- **D10 — Poll inclusion rules** (internal/partisan polls, population priority,
  field-date window; CLAUDE.md B4). **OPEN → decide at 2.1.**

## Current-state snapshot

Legend: ✅ done · 🟡 partial · ❌ missing

| Area                        | State                                              |
| --------------------------- | -------------------------------------------------- |
| Repo scaffold (uv, src, CI) | 🟡 pre-commit verified; GitHub Actions not yet run |
| Model config                | 🟡 typed loader done; most values provisional      |
| Handoff contract            | ❌ not drafted                                     |
| FiftyPlusOne polls          | ❌ not downloaded; ToS unchecked                   |
| District leans (2026 maps)  | ❌ source candidate: Downballot                    |
| House race metadata         | ❌ no source chosen (B9)                           |
| Senate races + holdovers    | ❌ not compiled                                    |
| Historical results (2022)   | ❌ not downloaded                                  |
| Generic ballot average      | ❌ missing                                         |
| Senate poll averages        | ❌ missing                                         |
| House fundamentals prior    | ❌ missing                                         |
| Senate prior + combine      | ❌ missing                                         |
| Simulator + seat accounting | ❌ missing                                         |
| 2022 backtest               | ❌ missing                                         |
| Frozen artifact + tag       | ❌ missing                                         |

## Pinned facts (don't rediscover these)

**Engineering conventions (user requirements; also in CLAUDE.md)**

- TDD: failing test → confirm red → minimal code → green → refactor. Before
  refactoring existing code, add characterization tests first.
- Clean Code: short single-purpose functions with verb names; module helpers are
  `_private`.
- Pre-commit (`.pre-commit-config.yaml`) runs ruff check, ruff format --check,
  ty check, and pytest via `uv run`; GitHub Actions (`.github/workflows/ci.yml`)
  runs the same on every push/PR. Never `--no-verify`.
- ty gotcha: type-only imports (e.g. `_typeshed.DataclassInstance` under
  `if TYPE_CHECKING:`) must be quoted in parameter annotations; Python 3.12
  evaluates them at import → NameError. PEP 695 bounds (`[T: X]`) are lazy and
  safe unquoted.

**Repo & branches**

- GitHub: `msburns24/midterm-elections-2026` (public, default `main`).
- One local branch per area, cut from `main`; the user commits and merges at the
  end of each phase. Branches: `forecast/config` (0.3–0.4), `forecast/data`
  (P1), `forecast/polls` (P2), `forecast/priors` (P3), `forecast/simulate` (P4),
  `forecast/backtest` (P5), `forecast/freeze` (P6).
- Before starting a step, confirm you're on its phase branch
  (`git branch --show-current`).

**Schedule (soft targets)**

- Phase 0–1 by 2026-10-26 · Phase 2–3 by 10-29 · Phase 4 by 10-31 · Phase 5 by
  11-01 · Phase 6 (freeze) by the evening of 11-02 · Election Day 11-03.
- Cut order if behind: dashboard map (other plan) → backtest (Phase 5). Never
  cut control odds or the handoff artifact.

**Data**

- FiftyPlusOne files: `senate_general.csv`, `house_general.csv`, `generic.csv`,
  `pollsters.csv`, `sponsors.csv`, `races.csv`, `candidates.csv`. Race files
  have one row per candidate answer (`question_id`, `party`, `candidate_id`,
  `pct`, `hypothetical`); `generic.csv` has `dem`/`rep`. Shared columns:
  `pollster_id`, `sample_size`, `population` (a/rv/lv/v), `internal`,
  `partisan`, `tracking`, `start_date`, `end_date`. Verify against the actual
  download at 1.2.
- Leans calculated on old district lines are invalid for 2026 (10 states
  redrew).
- Don't hardcode incumbents, holdovers, leans, or rules. Load them from
  documented source files (CLAUDE.md rule).

**Model**

- Config: `config/model.toml` → `midterms.config.load_config()` → `ModelConfig`
  (frozen dataclasses). Adding a key means updating both the TOML and the
  dataclass, or the loader rejects it. `DEFAULT_PATH` resolves relative to the
  source tree, so it relies on uv's editable install.
- When a step sets a PROVISIONAL value, drop the tag and log the rationale in
  the Progress log.

- Target: Democratic two-party margin per race (CLAUDE.md C1 default from the
  reference approach; confirm at 3.1 if it's still open).
- `m_i = mu_i + eta + lambda_i * f + eps_i`; eta is Student-t (national), f is
  the light factor (D8), eps_i is race noise.
- Real-world poll error is about 2× sampling error (Shirani-Mehr et al. 2018),
  so inflate poll variance and add a per-race bias floor.

**Handoff gotcha (affects D7 and the election-night plan)**

- Conditioning by keeping only draws consistent with the calls: P(a draw matches
  k calls) shrinks fast. With 10k draws and about 15+ calls, few or no draws
  survive. So the artifact must carry the model _parameters_ (mu_i, sigma_i,
  lambda_i, national/factor distributions). That lets the laptop re-simulate
  with large S and condition properly (e.g., importance weighting on eta/f).

## Target structure

```
pyproject.toml  uv.lock  README.md  LICENSE  .gitignore
config/model.toml            # weights, half-life, error scales, S, seed
data/raw/<source>/<YYYY-MM-DD>/   # immutable pulls (gitignored if ToS requires)
data/processed/               # races.parquet, polls_clean.parquet, ...
src/midterms/
  sources/   fiftyplusone.py  leans.py  metadata.py  results.py
  polls.py        # generic-ballot + Senate averages
  prior.py        # House/Senate fundamentals
  combine.py      # precision-weight prior + polls
  simulate.py     # correlated draws, seat accounting, control
  rules.py        # GA/RCV/top-two/LA, holdovers, thresholds
  backtest.py
  export.py       # handoff artifact (D7 contract)
scripts/  fetch_data.py  build_races.py  run_forecast.py  backtest_2022.py
tests/
outputs/frozen/<tag>/        # handoff artifact + manifest
```

## Build order (one unit at a time)

### Phase 0 — Scaffold & contract

- [x] **0.1** `uv init` src-layout package `midterms`, Python 3.12, ruff +
      pytest, `.gitignore`, LICENSE (D9). — ✅ 2026-10-24 _Check:_
      `uv run pytest` and `uv run ruff check` both pass on an empty smoke test.
- [x] **0.2** Create the GitHub repo (public), first commit (user commits),
      push. — ✅ 2026-10-24 _Check:_ `gh repo view` shows it public with
      CLAUDE.md + scaffold.
- [x] **0.3** `config/model.toml` + a loader returning a typed config. — ✅
      2026-10-24 _Check:_ a test loads the config and asserts the keys/types.
- [ ] **0.4** Draft the handoff contract (D7) in `docs/handoff.md`: file names,
      columns, dtypes. _Check:_ the user approves it; the schema is copied into
      Pinned facts.
- [ ] **0.5** User commits + merges `forecast/config`, pushes `main`. _Check:_
      `gh run list` shows the first CI run green on `main`.

### Phase 1 — Data acquisition (research first)

- [ ] **1.1** Read the FiftyPlusOne ToS; decide commit vs. gitignore; record it
      in CLAUDE.md E11. _Check:_ decision logged; `.gitignore` matches it.
- [ ] **1.2** `fetch_data.py` pulls FiftyPlusOne into a dated raw folder.
      _Check:_ all 7 files present; real columns match Pinned (fix Pinned if
      not).
- [ ] **1.3** Acquire 2026-map district leans (Downballot) and load them.
      _Check:_ 435 rows, unique `state+district`, no null lean.
- [ ] **1.4** Research + pick the House metadata source (B9): incumbent party,
      open seat, uncontested, nominees. _Check:_ choice logged; coverage
      measured (rows with complete metadata / 435).
- [ ] **1.5** Load the Senate race list, holdovers by party, independents'
      caucus, VP tiebreak, all from a source. _Check:_ holdovers + races-up =
      100 seats.
- [ ] **1.6** Download MEDSL House 2022 results + 2022-map leans for the
      backtest. _Check:_ 435 districts joined to leans with zero unmatched.
- [ ] **1.7** `build_races.py` writes `data/processed/races.parquet` (one row
      per race). _Check:_ 435 House + all Senate rows; key columns non-null.

### Phase 2 — Polls

- [ ] **2.1** Poll cleaning per D10 (population priority, internal/partisan
      handling, hypotheticals, window). _Check:_ row counts before/after each
      filter printed and sane.
- [ ] **2.2** Generic-ballot weighted average (recency half-life, sample-size
      cap). _Check:_ value within ~2 pts of a public average on the same date.
- [ ] **2.3** Senate per-race two-party margin averages + effective poll count.
      _Check:_ every polled Senate race has a margin; spot-check 3 by hand.

### Phase 3 — Priors & combine

- [ ] **3.1** Fit House fundamentals (margin ~ lean + national env + incumbency)
      on historical data. _Check:_ coefficients and residual SD printed; signs
      sensible.
- [ ] **3.2** Apply it to 2026 → House `mu_i`, `sigma_i`; handle uncontested
      seats. _Check:_ 435 rows; the implied national seat expectation is
      plausible.
- [ ] **3.3** Senate prior (state lean + national + incumbency). _Check:_ prior
      for every Senate race; sanity-check vs. state partisanship.
- [ ] **3.4** Precision-weight Senate prior + polls (inflated poll error +
      floor). _Check:_ more polls → closer to the poll average; unpolled races →
      the prior.

### Phase 4 — Simulation

- [ ] **4.1** Pick the light factor (D8) + loadings; set eta (t, df), f, and eps
      scales in config. _Check:_ decision logged; config loads.
- [ ] **4.2** `simulate.py`: S correlated draws of all race margins (shared
      eta/f across chambers). _Check:_ empirical eta SD and race correlations
      match config within tolerance.
- [ ] **4.3** `rules.py`: special rules (GA runoff, ME/AK RCV, CA/WA top-two,
      LA) from verified sources. _Check:_ unit tests per rule; same-party CA/WA
      races resolve deterministically.
- [ ] **4.4** Seat accounting + control (holdovers, caucus, VP tiebreak, 218).
      _Check:_ unit tests on hand-built scenarios (50–50, 217/218).
- [ ] **4.5** `run_forecast.py` end to end → per-race P(win), seat
      distributions, P(control). _Check:_ numbers within a plausible band of
      public benchmarks; outliers explained.

### Phase 5 — Backtest (cut second)

- [ ] **5.1** Run the House pipeline on 2022 (as-of inputs). _Check:_ Brier, log
      loss, seat error, 80% interval coverage printed.
- [ ] **5.2** Adjust error scales if coverage is badly off; re-run 4.5. _Check:_
      2022 coverage within ~10 pts of nominal; change logged.

### Phase 6 — Export & freeze

- [ ] **6.1** `export.py` writes the handoff artifact per the 0.4 contract.
      _Check:_ a fresh loader script reads it and reproduces P(control).
- [ ] **6.2** README methods summary + data attributions. _Check:_ every source
      used is named with license/terms.
- [ ] **6.3** Final pull at the cutoff, run, manifest (data hashes, config,
      commit), git tag. _Check:_ `git tag` exists; artifact hash matches the
      manifest.

## Progress log

### 2026-10-24

- **Plan created.** Started from a blank repo (CLAUDE.md only, no commits).
  Scope comes from the /plan-clarify brief. CLAUDE.md Decision log updated with
  A1–A3, A5–A7, B1, E1–E3, E11, E13 + plan split. Open: D6 exact cutoff, D7
  handoff format, D8 factor, D9 license, D10 poll rules. The election-night plan
  is not created yet; it depends on the 0.4 contract.
- **Election-night plan created** at `.claude/plans/election-night.md`. It
  consumes this plan's 0.4 contract and 6.1 artifact.
- **0.1 done.** `uv init --lib` (Python 3.12.3) → `src/midterms/`; dev deps
  pytest 9.1 + ruff 0.17 (rules E,F,I,B,UP; line length 88); MIT LICENSE +
  `pyproject` license fields; `.gitignore` ignores `.venv`, caches, `data/raw/`,
  `.claude/settings.local.json` (plans stay tracked); README stub. Verified:
  `uv run pytest` 1 passed, `ruff check` and `ruff format --check` clean, and
  `git status --ignored` shows the venv and caches ignored. Next: 0.2, create
  the public GitHub repo; the user makes the first commit.
- **0.2 done.** The user committed `0a8effa` ("Scaffold 2026 midterm forecast
  project and plans") and pushed it to `msburns24/midterm-elections-2026`.
  Verified: `gh repo view` reports PUBLIC with default branch `main`; the remote
  holds all scaffold files; local `main` tracks `origin/main`. A8 (repo name)
  resolved. Adopted one branch per area/phase and created `forecast/config` for
  0.3–0.4. Next: 0.3, `config/model.toml` + typed loader.
- User decision: merge at the end of every phase in both repos (election-night
  Pinned updated).
- **0.3 done** (on `forecast/config`). `config/model.toml` has sections
  simulation, polls, poll_error, national, factor, race_noise. Every undecided
  value is tagged `PROVISIONAL: <decision>, set at <step>`; election rules are
  deliberately excluded (they come from data). `src/midterms/config.py` loads it
  into frozen dataclasses with strict validation (missing/unknown keys →
  KeyError, wrong type → TypeError, int→float widening). Verified: 5 tests pass
  (load + 3 rejection cases); ruff clean; the real file loads with the expected
  values. Next: 0.4, handoff contract.
- **0.3 follow-ups (user requests before closing 0.3).** (1) TDD adopted. Five
  characterization tests were added for the existing loader (int→float widening,
  bool rejected for int/float, non-string list, missing section), all green
  before refactoring. (2) `config.py` refactored to Clean Code style:
  `load_config` → `_read_toml`, `_build_dataclass`, `_require_exact_keys`,
  `_convert_value`, `_convert_string_list`, `_convert_float`, `_require_type`,
  each a few lines; still green. Then red→green on a new case: a non-table
  section used to raise AttributeError and now raises TypeError. (3) Added a
  pre-commit dev dep, `.pre-commit-config.yaml` (local uv hooks: ruff check,
  ruff format --check, pytest), installed the hook, and added GitHub Actions
  `ci.yml` (checkout@v4, setup-uv@v6, `uv sync --locked`, same three checks).
  Verified: `pre-commit run --all-files` passes; a probe file with an unused
  import and bad formatting fails ruff check + format (exit 1), then was
  deleted; 11 tests pass. The Actions workflow is unverified until the first
  push → new step 0.5. Conventions recorded in CLAUDE.md (How to work, E9/E10
  decisions) and Pinned.
- **Static typing added (user request).** Dev dep `ty` 0.0.91. The first
  `ty check` was red: two `invalid-argument-type` errors, a bare `type` passed
  to `dataclasses.fields`. Fixed by making `_build_dataclass` generic
  (`[T: DataclassInstance]`, returns `T`, so `load_config` is precisely typed)
  and typing `_require_exact_keys` as `type[DataclassInstance]`. That briefly
  broke pytest with a NameError (eager annotation of a TYPE_CHECKING-only name),
  fixed by quoting it. ty was added to the pre-commit hooks and CI. Verified: a
  probe `double("a")` fails the ty hook; `pre-commit run --all-files` passes all
  four hooks; 11 tests pass. CLAUDE.md E10 resolved.
