# Handoff contract: frozen forecast → election night

**Schema version:** 1.0 (approved 2026-10-24, forecast plan step 0.4)

The forecast pipeline writes one artifact directory at freeze time. The
election-night pipeline reads only this directory. It never imports forecast
internals. Any change to the files or columns below bumps `schema_version`.

## Conventions

- **Margin:** Democratic-side minus Republican-side two-party margin, in
  percentage points. Positive means the D side wins.
- **D side / R side:** the two finalists modeled in each race. Usually D vs. R,
  but the D side can be an independent the model treats as the anti-R candidate
  (who they caucus with is recorded per race). Same-party races are deterministic.
- **race_id:** `H-<ST>-<NN>` for House (`H-CA-12`; at-large `H-AK-00`) and
  `S-<ST>-<class>` for Senate (`S-GA-2`; a special election for a class 3 seat is
  `S-OH-3`). Unique even when a state has two Senate races.
- All values that describe election rules (seats, holdovers, thresholds,
  tiebreaks) come from documented sources at build time, never from code.

## Model the parameters describe

For draw `s` and race `i` in factor group `g(i)`:

```
margin[s, i] = mu[i] + eta[s] + factor_loading[i] * f[s, g(i)] + eps[s, i]
eta[s]       ~ scale_national * StudentT(df)        # shared by all races
f[s, g]      ~ Normal(0, scale_factor)               # one per group, iid
eps[s, i]    ~ Normal(0, sigma_race[i])              # independent per race
```

**Why this matters on election night:** given the latents `(eta, f)`, races are
independent, so the chance that a draw matches the calls has a closed form:
`P(D wins i | eta, f) = Phi((mu_i + eta + lambda_i * f_g) / sigma_race_i)`.
Weighting each latent draw by the product over called races conditions exactly.
It doesn't collapse the way filtering full draws does, because the latent space
is low-dimensional (1 + number of groups).

## Files in `outputs/frozen/<tag>/`

### `manifest.json`

| Key                | Type        | Meaning                                         |
| ------------------ | ----------- | ----------------------------------------------- |
| `schema_version`   | str         | `"1.0"`                                         |
| `tag`              | str         | git tag of the freeze, e.g. `forecast-2026-11-02` |
| `git_commit`       | str         | full SHA the artifact was built from            |
| `created_at`       | str         | ISO 8601 UTC timestamp                          |
| `config_sha256`    | str         | hash of `config/model.toml` used                |
| `data_snapshots`   | dict[str, str] | raw-source folder → sha256 of its contents   |
| `files`            | dict[str, str] | each artifact file → sha256                  |
| `n_draws`, `seed`  | int         | simulation settings used                        |

### `params.json`

```json
{
  "national": {"distribution": "student_t", "df": 5.0, "scale": 3.0},
  "factor": {"kind": "region", "scale": 2.0, "groups": ["northeast", "..."]}
}
```

Same semantics as the `[national]` and `[factor]` config sections, with the
final (non-provisional) values.

### `races.parquet`: one row per race on the 2026 ballot

| Column            | dtype     | Meaning                                                      |
| ----------------- | --------- | ------------------------------------------------------------ |
| `race_id`         | string    | key (see Conventions)                                        |
| `chamber`         | string    | `house` / `senate`                                           |
| `state`           | string    | USPS code                                                    |
| `district`        | Int16     | House district (0 = at-large); null for Senate               |
| `display_name`    | string    | e.g. `CA-12`, `Georgia (Class 2)`                            |
| `mu`              | float64   | expected margin (points)                                     |
| `sigma_race`      | float64   | SD of `eps` (points), > 0                                    |
| `factor_group`    | string    | one of `params.factor.groups`                                |
| `factor_loading`  | float64   | lambda_i                                                     |
| `contest_type`    | string    | `contested` / `uncontested` / `same_party`                   |
| `fixed_winner`    | string    | `D`/`R`/`I` for uncontested or same-party; null otherwise    |
| `d_side_caucus`   | string    | caucus if the D side wins (`D`, or `R`/`none` for unusual independents) |
| `r_side_caucus`   | string    | caucus if the R side wins (normally `R`)                     |
| `incumbent_party` | string    | `D` / `R` / `I` / `open`                                     |
| `rule`            | string    | `plurality` / `majority_runoff` / `rcv` / `top_two`          |
| `p_d_win`         | float64   | frozen marginal P(D side wins), for display and checks       |

### `chamber_rules.json`

```json
{
  "house":  {"total_seats": 435, "majority": 218},
  "senate": {"total_seats": 100, "holdovers": {"D": 0, "R": 0, "I_caucus_D": 0},
             "tiebreak_caucus": "R"}
}
```

Numbers are placeholders. Real values come from the sources pinned in forecast
step 1.5. `majority` is the seat count needed for control; the Senate's is
50 + tiebreak.

### `latent_draws.parquet`

One row per draw `s`: `eta` (float64) plus one `f_<group>` column per factor
group. These are the draws the election night conditions on.

### `draws.parquet` (verification only, gitignored)

One row per draw, one float32 column per `race_id` (the simulated margin).
Used to check that a zero-call re-sim reproduces the frozen numbers. The
election night doesn't need it. It's about 38 MB at S = 20 000, so it's
**gitignored**. Its sha256 stays in `manifest.json`, and the committed
script `scripts/reproduce_draws.py <artifact_dir>` regenerates it from the
committed files alone: `races.parquet` + `latent_draws.parquet` + the
manifest's `seed`, which drives the `eps` draws. The script checks the result
against the manifest hash (forecast plan step 6.2).

## Calls and race status (for reference)

The election night owns `calls.csv`. Its `winner` values are `D`, `R`, or
`runoff`. Each race on the dashboard has exactly one status:

| Status    | Meaning                                         | Effect on control odds        |
| --------- | ----------------------------------------------- | ----------------------------- |
| `uncalled` | no call yet                                    | simulated                     |
| `called`  | winner `D` or `R`                               | fixed to the winner           |
| `runoff`  | majority-rule race (GA) heading to a runoff     | still simulated (unresolved)  |
| `fixed`   | uncontested / same-party (`fixed_winner` set)   | fixed from the start          |
