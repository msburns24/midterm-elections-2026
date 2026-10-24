# Election-night plan

**Goal:** A live dashboard page on matthewburns.net. Before Nov 3 it shows the
frozen forecast; on election night it tracks race calls. A script on the user's
laptop pulls calls from a free source (manual `calls.csv` as fallback and
override), re-simulates with called races locked in using the frozen forecast
artifact, and publishes a `results.json`. The page polls it and shows: P(D
House) / P(D Senate) and seat distributions; odds over the night; a race table;
and a map / key-races panel (first to cut). Done = **a dry run before Nov 3: add
a fake call to `calls.csv` and within about 2 minutes the live page shows
updated control odds**; then it runs for real on the night of 2026-11-03.

**How to use this doc (multi-session):** work one unit at a time. Each step has
a checkbox and an acceptance check; when it passes, tick it and add a dated line
to the Progress log — the log is the _only_ home for narrative. At the start of
a session, read the Current-state snapshot + the first unchecked step and resume
there. Keep every section within its length cap (noted below); a `prettier` hook
auto-formats this file on save, so don't hand-align tables or fuss over
wrapping.

## Why this exists (problems to fix)

1. Nothing turns race calls into updated control odds; the forecast plan only
   produces a frozen artifact.
2. No free, automatable source of race _calls_ has been identified yet; most
   free feeds give vote counts, not calls.
3. The site is static (Quarto on Netlify), so updates must arrive as published
   JSON. No path has been chosen or measured that meets the ~2-minute target.
4. Naively filtering frozen draws collapses after about 15 calls, so a proper
   conditional re-sim is needed.
5. No dashboard page exists on matthewburns.net.
6. The night has to survive a broken scraper, a crashed loop, or a wrong call
   without a code change (manual override + runbook).
7. There's a hard deadline: it must work before the first polls close on
   2026-11-03.

## Decisions log

- **D1 — Architecture.** Laptop poller + re-sim → `results.json` → static OJS
  page. **RESOLVED (2026-10-24) → laptop + static JSON** because Actions cron
  lags, Netlify functions are JS-only, and HF/Streamlit sleep.
- **D2 — Call source.** Wikipedia scrape vs. own call rule on state feeds vs.
  other free source. **OPEN → decide at 1.2** after research; fallback is a
  hand-edited `calls.csv`.
- **D3 — Where `results.json` is served.** Commit to site repo vs. separate
  Netlify data site via CLI vs. raw GitHub (≈5 min cache). **OPEN → decide at
  0.2** by measured latency.
- **D4 — Conditioning method.** Importance-weight on national/factor draws vs.
  large-S rejection vs. analytic. **OPEN → decide at 2.2**; it depends on the
  forecast plan's D7 handoff format.
- **D5 — Manual vs. scraped precedence.** Proposal: a manual row always beats
  the scraper; manual can also "uncall" a race. **OPEN → decide at 1.3.**
- **D6 — Pre-election page.** **RESOLVED (2026-10-24) → page is public before
  Nov 3 showing the frozen forecast**, then flips to live mode.
- **D7 — Dashboard tech.** **RESOLVED (2026-10-24) → Quarto page with OJS +
  Observable Plot** in the existing site repo, following
  climate-commodity-risk's precedent.

## Current-state snapshot

Legend: ✅ done · 🟡 partial · ❌ missing

| Area                        | State                                             |
| --------------------------- | ------------------------------------------------- |
| Handoff contract (forecast) | ❌ blocked on forecast plan step 0.4              |
| Mock artifact for dev       | ❌ missing                                        |
| JSON publish path           | ❌ candidates listed; none measured               |
| Call source                 | ❌ not researched                                 |
| `calls.csv` + merge logic   | ❌ missing                                        |
| Conditional re-sim          | ❌ missing                                        |
| `results.json` writer       | ❌ schema not drafted                             |
| Poller loop                 | ❌ missing                                        |
| Dashboard page (site repo)  | ❌ missing; OJS precedent exists in the site repo |
| Dry run / runbook           | ❌ missing                                        |

## Pinned facts (don't rediscover these)

**Branches**

- One local branch per area, cut from `main`; the user commits and merges at the
  end of each phase. This repo: `live/contract` (P0), `live/calls` (P1),
  `live/resim` (P2), `live/poller` (P3), `live/rehearsal` (P5). Site repo:
  `midterms-dashboard` for P4. Merge at the end of every phase in both repos
  (user decision); in the site repo, merging to `main` deploys.

**Site repo**

- Path: `~/programming/repos/website` (remote `msburns24/website`). Quarto
  website, theme sandstone + `theme-light.scss`/`theme-dark.scss`.
- Netlify serves the **committed `_site/`** (no `netlify.toml`, no
  `_publish.yml`); live at matthewburns.net / msburns.netlify.app.
- `.gitignore` ignores `**/data/`, with explicit `!` re-includes per project. A
  new dashboard's data folder needs the same treatment.
- Precedent: `projects/climate-commodity-risk/dashboard.qmd` uses `{ojs}` +
  `FileAttachment(...)` + `Plot.plot`. FileAttachment is bundled at build time,
  so live data needs `fetch(url)` in a polling generator instead.

**Latency budget (target ≤ ~2 min from call → page)**

- Source lag (outside our control) + poll interval + re-sim + publish + CDN
  cache + page poll interval. Measure each at 0.2 / 2.3 / 5.1.
- raw.githubusercontent.com serves `Cache-Control: max-age=300` (≈5 min). That
  alone breaks the target unless cache-busted. Verify at 0.2.
- Committing every update to the site repo means hundreds of commits on the
  night and a deploy per push. That's a reason to prefer a separate data path.

**Election night**

- First polls close 18:00 ET (parts of IN/KY); last close 01:00 ET (AK)
  _(verify)_. The poller must be running and verified before 18:00 ET on
  2026-11-03.
- Fallback for any failure: edit `calls.csv` by hand → the loop publishes it.

## Target structure

```
# this repo (midterm-elections-2026)
data/live/calls.csv           # race_id, winner_party, called_at, source, note
data/live/calls_scraped.csv   # scraper output (never hand-edited)
src/midterms/live/
  artifact.py    # load frozen handoff artifact (or mock)
  calls.py       # fetch from source, merge with manual (D5)
  condition.py   # conditional re-sim (D4)
  results.py     # build results.json + append timeline
  publish.py     # push JSON per D3
scripts/  make_mock_artifact.py  run_live.py  dry_run.py
docs/election-night-runbook.md

# site repo (website)
projects/midterms-2026/index.qmd   # the dashboard page (OJS)
```

## Build order (one unit at a time)

### Phase 0 — Contract & plumbing recon

- [ ] **0.1** Draft the `results.json` schema (control odds, seat distributions,
      races, timeline, status, `updated_at`). _Check:_ the user approves it; the
      schema is pinned here.
- [ ] **0.2** Measure publish paths (D3): push a tiny timestamped JSON each way
      and time until the browser sees it. _Check:_ latencies logged; D3
      resolved.
- [ ] **0.3** Adopt the forecast handoff contract (forecast plan 0.4) and write
      `make_mock_artifact.py`. _Check:_ the mock loads via `artifact.py` and
      matches the contract dtypes.

### Phase 1 — Race calls

- [ ] **1.1** Research free call sources (Wikipedia API, state ENR feeds,
      others): ToS, lag, structure. _Check:_ a comparison table is pinned here.
- [ ] **1.2** Pick a source (D2); prototype a fetch against a past cycle (2024
      pages). _Check:_ the parsed calls map to `race_id` for ≥ 95% of races.
- [ ] **1.3** `calls.py`: merge scraped + manual per D5 → effective calls.
      _Check:_ tests: manual overrides scraped; uncall works; unknown race_id
      rejected.

### Phase 2 — Conditional re-sim & results

- [ ] **2.1** `artifact.py` loader for the frozen artifact (mock until forecast
      6.1 lands). _Check:_ zero calls → reproduces the artifact's P(control).
- [ ] **2.2** `condition.py` with the D4 method; called races fixed. _Check:_
      effective sample size stays healthy with 100+ random calls; the called
      races have P = 0/1.
- [ ] **2.3** Time the re-sim at a realistic call count. _Check:_ runtime < ~20
      s with 300 calls.
- [ ] **2.4** `results.py` writes `results.json` per the 0.1 schema + appends to
      the timeline. _Check:_ the JSON validates against the schema; the timeline
      grows by one point per run.

### Phase 3 — Poller loop

- [ ] **3.1** `publish.py` per D3. _Check:_ a run publishes and the public URL
      returns the new `updated_at`.
- [ ] **3.2** `run_live.py` loop: fetch → merge → re-sim → write → publish every
      N s. _Check:_ runs 30 min unattended against the mock with no errors.
- [ ] **3.3** Failure handling: source down / parse error keeps the last good
      calls, logs, and continues. _Check:_ kill the network mid-loop; the loop
      recovers and the page shows a stale-data warning.

### Phase 4 — Dashboard page (site repo)

- [ ] **4.1** `projects/midterms-2026/index.qmd` skeleton: OJS polling `fetch`
      of `results.json`, `updated_at` shown. _Check:_ `quarto preview` shows the
      timestamp changing when the JSON changes.
- [ ] **4.2** Headline panel: P(D House), P(D Senate), seat histograms, called
      tally. _Check:_ values match `results.json`; correct in light and dark.
- [ ] **4.3** Odds-over-the-night line chart from the timeline. _Check:_ a
      simulated 10-point timeline renders with time axis in ET.
- [ ] **4.4** Race table: competitive races, P(D), margin, status/winner,
      sortable. _Check:_ called rows visibly marked; works on phone width.
- [ ] **4.5** Map / key-races panel (cut first). _Check:_ the Senate map colors
      match the called/uncalled state.
- [ ] **4.6** Deploy the page to matthewburns.net in frozen-forecast mode.
      _Check:_ the live URL loads with the mock or real frozen forecast.

### Phase 5 — Rehearsal & go-live

- [ ] **5.1** **Done-signal dry run:** add a fake call to `calls.csv` on the
      live pipeline. _Check:_ the live page updates control odds within ~2 min.
- [ ] **5.2** Stress replay: script ~150 calls over 20 min. _Check:_ no crashes;
      latency stays within target; odds move monotonically sensibly.
- [ ] **5.3** Write `docs/election-night-runbook.md` (start, override, restart,
      rollback). _Check:_ the user follows it cold to start the loop.
- [ ] **5.4** Swap in the real frozen artifact, clear the fake calls, reset the
      timeline. _Check:_ the live page shows the frozen forecast with 0 calls.
- [ ] **5.5** Election night: loop running and verified before 18:00 ET
      2026-11-03. _Check:_ the first real call appears on the page.
- [ ] **5.6** After the night: archive `calls.csv` + the timeline; page left in
      final state. _Check:_ archive committed; page shows final results.

## Progress log

### 2026-10-24

- **Plan created.** The site repo was inspected: Netlify serves the committed
  `_site/`, and OJS precedent exists in climate-commodity-risk. It depends on
  the forecast plan (contract at its 0.4, artifact at its 6.1); development
  proceeds against a mock artifact until then. Open: D2 call source, D3 publish
  path, D4 conditioning, D5 override precedence.
