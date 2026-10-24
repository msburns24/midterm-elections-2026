# CLAUDE.md — 2026 Midterm Election Simulator

## What this project is

A project to build a probabilistic simulation of the 2026 US federal midterm elections (Election Day: Tuesday, November 3, 2026). The core idea is to estimate an expected outcome for each race from polls and/or fundamentals. Monte Carlo simulation with a correlated error structure then turns those estimates into distributions of race outcomes, seat counts, and chamber control.

Scope and top-level design were settled on 2026-10-24 (see **Decision log**). Many modeling details are still open. See **Open decisions** below.

## Status

- Created: 2026-10-24, ten days before Election Day.
- Phase: planning. No code or data yet. Work is split into two plans:
  - `.claude/plans/forecast-model.md`: data, model, backtest, freeze, handoff artifact.
  - `.claude/plans/election-night.md`: call source, laptop poller, conditional re-sim, dashboard on matthewburns.net (page lives in the site repo, `~/programming/repos/website`).

## How to work in this repo (instructions for Claude)

- Nothing under **Open decisions** has been decided. Do not choose an option for an OPEN decision on your own. Ask, then record the answer in the **Decision log** (date, choice, rationale) and update every section it affects.
- If a task depends on an open decision, name the decision and ask before proceeding. Do not silently fall back to a default.
- Do not hardcode facts that should come from data: incumbents, nominees, holdover seat counts, district leans, election rules. Pull them from a documented source or ask. Items marked *(verify)* are unconfirmed.
- Respect each data source's license and attribution requirements (see **Data sources**).
- **Test-driven development.** Write a failing test first, confirm it fails (red), write the minimum code to pass (green), then refactor with the tests green. When refactoring existing code, first add characterization tests that pin its current behavior.
- **Clean code (Robert C. Martin style).** Write short functions that each do one thing, with clear verb names (`load_config`, `require_exact_keys`, `convert_float`). Prefer extracting a well-named helper over adding a comment or a nested branch.
- **Pre-commit checks.** Never bypass them (`--no-verify`). If a hook fails, fix the cause.
- Keep this file current. When a decision is made, move it from **Open decisions** to the **Decision log** and fill in the affected sections (Commands, Repository layout, Key dates).

## Reference approach (discussed, not adopted)

This is the starting point from initial research. Every component is subject to the open decisions below.

1. **Target:** Democratic two-party margin per race.
2. **Poll average per race:** weight polls by recency, sample size, and pollster quality. Correct for house effects, adjust for likely voters vs. registered voters, and discount internal and partisan polls.
3. **Fundamentals prior per race:** this fills in unpolled races, which is most House districts. Regress past results on presidential lean relative to the nation, the national environment (generic ballot), incumbency, and possibly other features.
4. **Combine prior and polls,** for example with precision weighting. Poll uncertainty should reflect total survey error, not just the reported margin of error. Shirani-Mehr, Rothschild, Goel & Gelman (2018) found real-world poll error is roughly twice sampling error. Error also needs a floor, because polls of the same race share bias.
5. **Correlated error:**
   `m_i = mu_i + eta + sum_k(lambda_ik * f_k) + eps_i`
   - `eta`: national shock shared by all races.
   - `f_k`: demographic or regional factors, drawn once per simulation.
   - `lambda_ik`: race i's exposure to factor k.
   - `eps_i`: race-specific noise.
   - A fat-tailed distribution for the national term is a candidate.
6. **Simulate** S draws. Count seats including holdovers, then compute per-race P(win), seat distributions, P(control), tipping-point races, and conditional probabilities.
7. **Validate** via backtests (e.g., 2018, 2022), Brier score, log loss, calibration plots, and interval coverage.

538's model tiers are useful for scoping:

- **Lite:** polls only.
- **Classic:** polls plus fundamentals.
- **Deluxe:** classic plus expert ratings.

## Data sources (FiftyPlusOne selected for polls; the rest are candidates)

### Polls (2026 cycle)

- **FiftyPlusOne** (fiftyplusone.news/downloads; schema documented at fiftyplusone.news/readme). Run by former 538 staff.
  - Files: `senate_general.csv`, `house_general.csv`, `governor_general.csv`, `generic.csv`, `pollsters.csv`, `sponsors.csv`, `races.csv`, `candidates.csv`.
  - Race poll files have one row per candidate answer (`question_id`, `party`, `candidate_id`, `pct`, `hypothetical`). `generic.csv` has `dem` and `rep` columns.
  - Shared columns include `pollster_id`, `sample_size`, `population` (a/rv/lv/v), `internal`, `partisan`, `tracking`, `start_date`, and `end_date`.
  - Computed averages (e.g., `generic_ballot_topline.csv`) and crosstabs are Premium/Enterprise only.
  - Check the terms of service before redistributing.
- **New York Times poll database.** Successor to 538's database, in roughly 538's format. Senate, House, governor, and approval downloads are available under CC BY 4.0, with attribution to The Times required.

### Pollster quality and historical polling error

- **Silver Bulletin pollster ratings.** Uses 538's methodology and includes a mean-reverted bias per pollster. Access terms: check.
- **Archived 538 data on DataHub** (datahub.io/fivethirtyeight/pollster-ratings). Includes a raw-polls file with each poll's actual margin, error, and bias, which is useful for calibrating error variances. Other 538 archives, such as historical generic ballot polls, are also on DataHub.

### District and state partisanship

- **The Downballot presidential results by congressional district** (the-db.co/presbycd). Updated for the 2026 lines, with older maps available for backtesting.
- Ten states drew new maps for 2026, covering about 40% of House seats. Leans calculated on old district lines are not valid for 2026.

### Historical results

- **MIT Election Data and Science Lab** (electionlab.mit.edu/data): House 1976–2024, plus Senate, president, and precinct-level returns.
- **Dave Leip's Atlas:** some files are available through university libraries, and licensing varies.

### Benchmarks (comparison only)

- Silver Bulletin FLIPR, FiftyPlusOne's forecast, Decision Desk HQ, The Economist, and the Cornell (Enns) House model.
- Expert ratings: Cook Political Report, Sabato's Crystal Ball, Inside Elections.
- Prediction markets.

### Not yet identified

- Authoritative 2026 nominee lists and uncontested races.
- Incumbency and open-seat status.
- Demographics for the new congressional districts.
- A 2026 results source for scoring.

## Open decisions

Every item below is **OPEN**. Resolved items have moved to the **Decision log**. Each open item lists the question, the options identified so far, and notes.

### A. Goals and scope

- **A4. Pre-election freeze (partly resolved):** a freeze will happen, around the evening of 2026-11-02, marked with a git tag. Still open: the exact cutoff time and timezone, and whether a content-hash manifest goes with the tag.

### B. Data

- **B2. Acquisition:** manual download or scripted fetch. Review each source's terms of use first.
- **B3. Snapshotting:** whether to keep date-stamped, immutable raw pulls.
- **B4. Poll inclusion rules:**
  - Internal and partisan polls: exclude, discount, or adjust.
  - Population priority when a poll reports several (LV, RV, adults).
  - Hypothetical matchups.
  - Multiple question versions in one poll (e.g., with or without leaners or third parties).
  - Overlapping tracking polls.
  - Minimum sample size and missing sample sizes.
  - Field-date window.
- **B5. Pollster quality:** Silver Bulletin ratings, 538 archive ratings, ratings built from raw-polls, or none.
- **B6. Partisan lean metric:** 2024 presidential margin relative to the nation, a 2020/2024 blend, or a composite that includes downballot races. Choose the source (Downballot, Dave's Redistricting App, other).
- **B7. Historical results:** MEDSL or Leip, and which cycles to train on.
- **B8. Historical polls for backtests:** the source, and how to reconstruct what was known as of each date.
- **B9. Race and candidate metadata:** a source for nominees, incumbency, open seats, uncontested races, and retirements. *(To be settled by a research step in the forecast plan. Candidates: FiftyPlusOne `races.csv`/`candidates.csv`, Ballotpedia, Wikipedia.)*
- **B10. Expert ratings:** whether to include them as a feature. If so, choose which raters, how to encode them, and whether to enter them manually or pull them from a source.
- **B11. Other fundamentals:** fundraising (FEC), candidate quality, demographics (ACS by district), presidential approval.
- **B12. Results for scoring:** AP calls, certified results, or a later MEDSL release. Also decide when scoring happens.

### C. Modeling

- **C1. Target variable:** two-party D margin, two-party D share, or multi-candidate shares.
- **C2. Poll averaging method:** weighted average plus house effects, or a Bayesian state-space (time-varying) model.
- **C3. Weighting parameters:** recency half-life, sample-size cap, and the functional form of the quality weight.
- **C4. House effects:** estimate them (e.g., a mixed model across races with shrinkage), reuse external bias estimates, or skip.
- **C5. Population adjustment:** whether and how to adjust adult and RV polls toward an LV basis.
- **C6. National environment:** build a generic-ballot average or use an external one. Decide how to map the generic ballot to the national House vote and how to represent its uncertainty.
- **C7. Fundamentals specification:** features, functional form, midterms only or all cycles, and whether House, Senate, and governor races get separate models.
- **C8. Combining polls and prior:** precision weighting or a joint Bayesian model. Decide how the prior's weight shrinks as poll volume grows.
- **C9. Poll error model:** the inflation factor for total survey error and the per-race bias floor.
- **C10. National error term:** distribution (normal or Student-t, and degrees of freedom if t), scale, and calibration data.
- **C11. Sub-national correlated error:** factor model, covariance from demographic similarity, or region effects. Choose which factors and their data source.
- **C12. Race-specific error:** whether it depends on poll count, days to election, candidate quality, or open-seat status.
- **C13. Calibration method:** how variances are fit (historical raw-polls, backtests, holdout cycles).
- **C14. Simulation settings:** number of draws and RNG seed policy.
- **C15. Special rules.** Confirm the current rules for each before modeling:
  - Georgia's majority requirement and runoffs.
  - Ranked-choice voting in Maine and Alaska.
  - Top-two primaries in California and Washington, including same-party general elections.
  - Louisiana's format *(verify)*.
  - Independents and minor-party candidates.
  - Uncontested seats and vacancies.
  - Senate special elections.
- **C16. Chamber control definitions:**
  - Senate holdover seats by party *(verify from source)*.
  - Which caucus each independent joins.
  - Handling of the Vice President's tiebreak.
  - House majority threshold, which is 218 of 435 when the chamber is full, and how vacancies change it.
- **C17. House–Senate joint simulation:** whether the chambers share the same national and factor draws in each simulation, or are simulated separately.

### D. Validation

- **D1. Metrics:** Brier score, log loss, calibration curve, interval coverage, seat-count error, margin RMSE.
- **D2. Benchmarks:** which forecasts to compare against, and whether to snapshot their numbers at freeze time.
- **D3. Acceptance criteria:** what must pass before the forecast is frozen.

### E. Engineering

- **E4. Probabilistic programming, if any:** PyMC, NumPyro, Stan via CmdStanPy, brms, or none.
- **E5. Plotting:** matplotlib, seaborn, plotly, altair, or ggplot2.
- **E6. Code organization:** a package (src layout) plus scripts, notebooks, or both. Set a notebook policy.
- **E7. Storage:** CSV, parquet, a DuckDB file, or other. Choose a directory layout (e.g., raw, interim, processed, outputs).
- **E8. Configuration:** where model parameters live (YAML, TOML, Python) and how runs are parameterized.
- **E9. Testing scope (partly resolved):** pytest with TDD (see Decision log). Still open: the scope of data-validation and regression tests.
- **E11. Committed vs. ignored data (partly resolved):** the repo is public on GitHub (see Decision log). Still open: which data files are committed and which are gitignored. This depends on each source's terms of service.
- **E12. Licensing (partly resolved):** the code is MIT (see Decision log). Still open: each data source's attribution and redistribution constraints.
- **E14. Reproducibility:** pinned dependencies and a per-run manifest (data snapshot, parameters, code hash).

## Decision log

| ID | Date | Decision | Rationale |
|----|------|----------|-----------|
| A1 | 2026-10-24 | Public live dashboard on matthewburns.net, a static Quarto site on Netlify. Headline: P(D House) and P(D Senate). | The user wants to watch it on election night and share it. |
| A2 | 2026-10-24 | All 435 House races and all 2026 Senate races, including specials. No governors. | Control of Congress is the focus. Governors don't affect it. |
| A3 | 2026-10-24 | One frozen pre-election forecast. On election night, race calls lock in winners, the remaining races are re-simulated, and the control odds update. No daily updates before the freeze. | Live control odds are the core feature. Daily updates don't fit 10 days. |
| A5 | 2026-10-24 | "Classic + light factor." Senate: poll average blended with a lean prior. House: district lean + generic ballot + incumbency. Error: fat-tailed national shock + one sub-national factor + race noise. No house effects or full factor model. | The full reference approach doesn't fit about 15 hours of work. Simple classic was judged slightly too thin. |
| A6 | 2026-10-24 | Dashboard panels: control odds and seat distributions; odds over the night; a race table; a map/key-races panel (first to cut). Static page fetching JSON, built with OJS/JS. | A static page never sleeps and handles traffic spikes. HF Spaces and Streamlit were rejected. |
| A7 | 2026-10-24 | A quick 2022 backtest of the House fundamentals model. Cut it if time runs short, after the map. | Sanity-checks the variances without a full validation program. |
| B1 | 2026-10-24 | FiftyPlusOne for Senate and generic-ballot polls. Check its ToS before committing raw data to the public repo. | Rich schema. Its `races.csv`/`candidates.csv` may also help with B9. |
| E1–E3 | 2026-10-24 | Python 3.12, uv, pandas/numpy. pytest and ruff. | Matches the user's tooling and is quick to build. |
| E11 | 2026-10-24 | Public GitHub repo, separate from the matthewburns.net site repo. | Portfolio visibility, and the model stays decoupled from the site build. |
| E13 | 2026-10-24 | Model runs locally. On election night, the poller and re-sim run on the user's laptop and push results JSON. | GitHub Actions cron can lag 10–30+ minutes when busy. Netlify functions are JS-only. |
| — | 2026-10-24 | Race calls come from free sources only, researched first (Wikipedia, state results feeds). A hand-edited `calls.csv` is the fallback. | Paid APIs (AP, DDHQ) cost $1k+ and need a sales process. |
| — | 2026-10-24 | Two plans: the forecast model (deadline: freeze around Nov 2) and election night (deadline: Nov 3). They connect through a pinned handoff-file contract. | Two separate deadlines. Lets each plan progress in parallel. |
| — | 2026-10-24 | Claude writes the code and the user reviews it, for this project only. | 10-day deadline. |
| A8 | 2026-10-24 | Repo name `midterm-elections-2026` (github.com/msburns24/midterm-elections-2026). | Matches the local folder. |
| — | 2026-10-24 | Git workflow: one local branch per project area/phase, cut from `main` (e.g., `forecast/data`, `live/calls`). The user commits and merges. The full branch list lives in each plan's Pinned facts. | The user asked for branches per area. Keeps `main` clean and phases reviewable. |
| E9 | 2026-10-24 | pytest, with test-driven development for all new code and characterization tests before refactors. | User requirement. |
| E10 | 2026-10-24 | ruff (lint and format), ty (static types), and pytest run as pre-commit hooks (`.pre-commit-config.yaml`, using uv-locked versions) and in GitHub Actions on every push and PR (`.github/workflows/ci.yml`). | User requirement: checks run before any commit. ty was the user's preference over mypy/pyright. It's pre-1.0, so the version is pinned by uv.lock. |
| — | 2026-10-24 | Code style: short, single-purpose functions with clear verb names (Robert C. Martin / Clean Code). | User requirement. |
| E12 (code) | 2026-10-24 | MIT license for the code. | Simplest choice for a public portfolio repo. Data terms are tracked per source. |
| — | 2026-10-24 | Done signal: a dry run before Nov 3. Add a fake call to `calls.csv`, and within about 2 minutes the live page updates its control odds. | Rehearse before the real night. |

## Commands

```bash
uv sync                 # create/refresh .venv from uv.lock
uv run pre-commit install         # once per clone: run ruff + pytest before each commit
uv run pre-commit run --all-files # run the hooks manually
uv run pytest           # tests (tests/)
uv run ruff check       # lint (rules E,F,I,B,UP)
uv run ruff format      # format
uv run ty check         # static type check
```

Pipeline commands are TBD as scripts land.

## Repository layout

TBD after E6–E7 are decided.

## Key dates

- 2026-10-24: project started.
- Freeze cutoff: around the evening of 2026-11-02. Exact time TBD (A4).
- Election-night dry run: before 2026-11-03.
- 2026-11-03: Election Day.
- Scoring date: TBD (B12).