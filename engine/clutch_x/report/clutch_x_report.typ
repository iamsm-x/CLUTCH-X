#let data = json("report-data.json")
#let orange = rgb("#FF5500")
#let ink = rgb("#11151C")
#let muted = rgb("#536171")
#let hairline = rgb("#D9DEE5")
#let pale = rgb("#F3F5F7")

#set page(
  paper: "a4",
  margin: (x: 17mm, y: 16mm),
  header: context [
    #text(size: 7pt, fill: muted, weight: "medium")[
      CLUTCH-X  /  T20 CONTEXTUAL LEVERAGE ENGINE
    ]
    #line(length: 100%, stroke: 0.5pt + hairline)
  ],
  footer: context [
    #line(length: 100%, stroke: 0.5pt + hairline)
    #align(right)[
      #text(size: 7pt, fill: muted)[
        METHODOLOGY REPORT  /  #counter(page).display("1")
      ]
    ]
  ],
)
#set text(font: "Libertinus Serif", size: 9pt, fill: ink)
#set par(leading: 0.68em, justify: true)
#set heading(numbering: none)

#let section(kicker, title) = [
  #v(10pt)
  #text(size: 8pt, weight: "bold", fill: orange)[#kicker]
  #heading(level: 2)[#title]
]

#let fixed(value, digits: 1) = str(calc.round(value, digits: digits))
#let pct(value) = fixed(value * 100, digits: 1) + "%"
#let delta(value) = (if value > 0 { "+" } else { "" }) + fixed(value, digits: 1)

#align(left)[
  #v(24pt)
  #text(size: 11pt, weight: "bold", fill: orange)[ANALYTICS WHITEPAPER]
  #v(8pt)
  #text(size: 38pt, weight: "bold", fill: ink)[CLUTCH-X]
  #v(4pt)
  #text(size: 17pt, fill: muted)[#data.subtitle]
  #v(16pt)
  #line(length: 100%, stroke: 3pt + orange)
  #v(18pt)
  #text(size: 12pt, weight: "bold")[
    A transparent, reproducible framework for identifying T20 players who
    execute above expectation in high-leverage moments.
  ]
  #v(14pt)
  #text(size: 9pt, fill: muted)[
    Dataset snapshot: #data.first_season to #data.latest_season.
    #data.delivery_count deliveries across #data.match_count matches and
    #data.competition_count competitions.
  ]
]

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 8pt,
  inset: 10pt,
  fill: pale,
  [*DELIVERIES*], [*MATCHES*], [*ELIGIBLE BATTERS*], [*ELIGIBLE BOWLERS*],
  [#data.delivery_count], [#data.match_count], [#data.eligible_batters], [#data.eligible_bowlers],
)

#v(14pt)
#block(
  fill: if data.rankings_meet_stability_target { rgb("#EAF5EF") } else { rgb("#FFF2E8") },
  stroke: (left: 3pt + orange),
  inset: 12pt,
)[
  #text(weight: "bold")[
    RANKING STABILITY:
    #if data.rankings_meet_stability_target [TARGET MET] else [BELOW TARGET]
  ]
  #linebreak()
  #text(size: 8pt)[
    The PRD requires split-half Spearman rho >= 0.65. The measured result is
    batting rho #fixed(data.split_half.at(0).rho, digits: 4) and bowling rho
    #fixed(data.split_half.at(1).rho, digits: 4). Rankings are exploratory
    and must not be presented as validated stable rankings.
  ]
]

#section("01 / DATA AND PRESSURE AUDIT", "Coverage and pressure separation")
The analysis scopes competition data to IPL and T20I, reconstructs the
pre-delivery match state, and excludes Super Overs and abandoned/no-result
matches with insufficient play. The dataset contains
#pct(data.high_pressure_share) high-pressure deliveries at the PI >= 60 cutoff.

#grid(
  columns: (1.3fr, 1fr, 1fr),
  gutter: 5pt,
  inset: 5pt,
  fill: pale,
  [*PRESSURE CHECK*], [*OBSERVED*], [*ACCEPTANCE*],
  [High-pressure share], [#pct(data.pressure_audit.high_pressure_share)], [15% to 25%],
  [High-pressure wicket rate], [#pct(data.pressure_audit.high_pressure_wicket_rate)], [Compare regimes],
  [Normal-pressure wicket rate], [#pct(data.pressure_audit.normal_wicket_rate)], [Reference],
  [Wicket-rate chi-square p], [#data.pressure_audit.wicket_rate_p_value], [< 0.01],
  [Run-variance Levene p], [#data.pressure_audit.run_variance_p_value], [< 0.01],
)

#v(8pt)
#text(size: 8pt, weight: "bold")[Pressure Index distribution (bin width: 5)]
#for bin in data.pressure_histogram {
  grid(
    columns: (36pt, 1fr, 48pt),
    gutter: 6pt,
    [#text(size: 7pt, fill: muted)[#bin.label]],
    [#box(width: bin.bar_width_pt * 1pt, height: 5pt, fill: orange)],
    [#align(right)[#text(size: 7pt, fill: muted)[#bin.count]]],
  )
}

#pagebreak()
#section("02 / SCORING METHODOLOGY", "How pressure and performance are measured")

#text(size: 11pt, weight: "bold")[Delivery-level Pressure Index]
#block(fill: pale, inset: 10pt)[
  *Second innings:* chase tension is
  100 x clip(RRR / par rate - 1, 0, 1)^2, weighted 75%; resource scarcity
  ((wickets lost / 9) x (1 - balls remaining / scheduled balls)) is weighted
  25%. *First innings:* PI is the greater of the early-collapse trigger and
  death-over urgency. Knockouts receive a 1.15 multiplier, then PI is clamped
  to 0-100. High pressure starts at PI 60; critical leverage starts at PI 80.
  Collapse pressure starts at 70 for three wickets lost by over 8 (+5 per
  additional wicket), or 75 for five wickets by over 14 (+4 per wicket).
  Death-over urgency starts at 30 in over 16 and increases 15 per over.
]

#v(8pt)
#text(size: 11pt, weight: "bold")[Context baselines and reliability]
Expected delivery outcomes are bucketed by format, season, innings, and match
phase; sparse buckets shrink toward the parent expectation using 30 prior
deliveries. A player needs at least 150 high-pressure balls and 10
high-pressure matches. Per-player pressure metrics shrink toward the eligible
peer mean with reliability weight
#block(fill: pale, inset: 8pt)[
  w = pressure balls / (pressure balls + 150)
]
Match-to-match consistency is adjusted as mean impact minus 0.5 times the
sample standard deviation. Batting impact is scaled per 100 balls; bowling
runs saved is scaled per six legal balls.

#v(8pt)
#text(size: 11pt, weight: "bold")[Rank construction]
Each component is percentile-ranked within its eligible discipline cohort.
Baseline ratings weight ordinary-condition performance; pressure ratings
weight reliability-adjusted pressure performance. The final score is:
#block(fill: pale, inset: 10pt)[
  Clutch-X = 0.55 x pressure rating
  + 0.25 x clip((net clutch delta + 100) / 2, 0, 100)
  + 0.20 x positive-impact rate (as a percentage).
]

#grid(
  columns: (1fr, 1fr),
  gutter: 8pt,
  [
    *Batting baseline:* 60% normal strike-rate percentile,
    20% boundary-rate percentile, 20% dot-ball-avoidance percentile.
    *Pressure rating:* 40% volatility-adjusted pRAE, 25% shrunk
    strike-rate delta, 10% boundary-rate delta, 10% dot-rate improvement,
    10% wicket preservation, 5% positive-impact rate.
  ],
  [
    *Bowling baseline:* 60% economy percentile, 20% dot-rate percentile,
    20% wickets-per-24-balls percentile. *Pressure rating:* 40%
    volatility-adjusted pRSAE, 25% shrunk economy delta, 10% dot-rate
    improvement, 20% clutch-wicket impact, 5% positive-impact rate.
  ],
)

#section("03 / STABILITY AUDIT", "Acceptance evidence")
The odd/even chronological match split is evaluated on eligible players only;
each half is volume-weighted before Spearman correlation. This dataset misses
the PRD acceptance threshold in both disciplines.

#grid(
  columns: (1.2fr, 0.8fr, 0.8fr, 0.8fr, 1fr),
  gutter: 5pt,
  inset: 5pt,
  fill: pale,
  [*DISCIPLINE*], [*ELIGIBLE*], [*SPLIT rho*], [*TARGET*], [*STATUS*],
  [Batting], [#data.split_half.at(0).eligible_players], [#fixed(data.split_half.at(0).rho, digits: 4)], [0.65], [#if data.split_half.at(0).meets_target [PASS] else [BELOW TARGET]],
  [Bowling], [#data.split_half.at(1).eligible_players], [#fixed(data.split_half.at(1).rho, digits: 4)], [0.65], [#if data.split_half.at(1).meets_target [PASS] else [BELOW TARGET]],
)

#section("04 / VERIFIED RANKINGS", "Batting Top 10")
These rows are read directly from the deterministic
`top10_batters.parquet` artifact. Ranks and player IDs are retained without
recalculation or re-sorting in the report layer.

#text(size: 8pt, weight: "bold")[Clutch-X score comparison (0-100)]
#for row in data.batting {
  let bowler = data.bowling.at(row.rank - 1)
  grid(
    columns: (1.3fr, 0.8fr, 1.3fr, 0.8fr),
    gutter: 6pt,
    [#text(size: 7pt)[B #row.rank #row.player_name]],
    [#box(width: row.clutch_x_score * 0.8pt, height: 5pt, fill: orange)],
    [#text(size: 7pt)[W #bowler.rank #bowler.player_name]],
    [#box(width: bowler.clutch_x_score * 0.8pt, height: 5pt, fill: rgb("#00A3FF"))],
  )
}

#grid(
  columns: (0.25fr, 1.35fr, 0.8fr, 1fr, 0.7fr, 0.8fr, 0.7fr, 0.9fr, 0.65fr),
  gutter: 4pt,
  [*#text(size: 6pt)[RANK]*], [*#text(size: 6pt)[PLAYER / ID]*],
  [*#text(size: 6pt)[HP BALLS / MATCHES]*], [*#text(size: 6pt)[SR BASE -> HP]*],
  [*#text(size: 6pt)[SR DELTA]*], [*#text(size: 6pt)[pRAE / 100]*],
  [*#text(size: 6pt)[POSITIVE]*], [*#text(size: 6pt)[BASE -> PRESSURE]*],
  [*#text(size: 6pt)[SCORE]*],
)
#for row in data.batting {
  grid(
    columns: (0.25fr, 1.35fr, 0.8fr, 1fr, 0.7fr, 0.8fr, 0.7fr, 0.9fr, 0.65fr),
    gutter: 4pt,
    inset: (y: 3pt),
    stroke: (bottom: 0.4pt + hairline),
    [#text(fill: orange, weight: "bold")[#row.rank]],
    [#row.player_name #text(size: 6pt, fill: muted)[(#row.player_id)]],
    [#row.high_pressure_balls_faced / #row.high_pressure_matches],
    [#fixed(row.normal_strike_rate) -> #fixed(row.high_pressure_strike_rate)],
    [#delta(row.strike_rate_delta)],
    [#delta(row.prae_per_100)],
    [#pct(row.positive_impact_rate)],
    [#fixed(row.baseline_rating) -> #fixed(row.pressure_rating)],
    [#text(weight: "bold")[#fixed(row.clutch_x_score)]],
  )
}

#pagebreak()
#section("04 / VERIFIED RANKINGS", "Bowling Top 10")
These rows are read directly from the deterministic
`top10_bowlers.parquet` artifact.

#grid(
  columns: (0.25fr, 1.35fr, 0.8fr, 1fr, 0.7fr, 0.8fr, 0.7fr, 0.9fr, 0.65fr),
  gutter: 4pt,
  [*#text(size: 6pt)[RANK]*], [*#text(size: 6pt)[PLAYER / ID]*],
  [*#text(size: 6pt)[HP BALLS / MATCHES]*], [*#text(size: 6pt)[ECONOMY BASE -> HP]*],
  [*#text(size: 6pt)[ECONOMY DELTA]*], [*#text(size: 6pt)[pRSAE / OVER]*],
  [*#text(size: 6pt)[WICKETS / POSITIVE]*], [*#text(size: 6pt)[BASE -> PRESSURE]*],
  [*#text(size: 6pt)[SCORE]*],
)
#for row in data.bowling {
  grid(
    columns: (0.25fr, 1.35fr, 0.8fr, 1fr, 0.7fr, 0.8fr, 0.7fr, 0.9fr, 0.65fr),
    gutter: 4pt,
    inset: (y: 3pt),
    stroke: (bottom: 0.4pt + hairline),
    [#text(fill: orange, weight: "bold")[#row.rank]],
    [#row.player_name #text(size: 6pt, fill: muted)[(#row.player_id)]],
    [#row.high_pressure_legal_balls / #row.high_pressure_matches],
    [#fixed(row.normal_economy, digits: 2) -> #fixed(row.high_pressure_economy, digits: 2)],
    [#delta(row.economy_delta)],
    [#delta(row.prsae_per_over)],
    [#row.high_pressure_wickets / #pct(row.positive_impact_rate)],
    [#fixed(row.baseline_rating) -> #fixed(row.pressure_rating)],
    [#text(weight: "bold")[#fixed(row.clutch_x_score)]],
  )
}

#section("05 / EXPOSURE AND PROVENANCE", "Audit trail")
Top-10 high-pressure exposure is summarized by competition and innings; it is
descriptive and does not impose a quota on the rank order.

#grid(
  columns: (1fr, 0.7fr, 1.2fr, 1.4fr),
  gutter: 5pt,
  inset: 5pt,
  fill: pale,
  [*DISCIPLINE*], [*COMPETITION*], [*INNINGS*], [*HP VOLUME / PLAYERS*],
)
#for row in data.batting_exposure {
  grid(
    columns: (1fr, 0.7fr, 1.2fr, 1.4fr),
    gutter: 5pt,
    inset: (y: 3pt),
    stroke: (bottom: 0.4pt + hairline),
    [Batting], [#row.competition_type], [#row.innings],
    [#row.high_pressure_volume / #row.represented_players],
  )
}
#for row in data.bowling_exposure {
  grid(
    columns: (1fr, 0.7fr, 1.2fr, 1.4fr),
    gutter: 5pt,
    inset: (y: 3pt),
    stroke: (bottom: 0.4pt + hairline),
    [Bowling], [#row.competition_type], [#row.innings],
    [#row.high_pressure_volume / #row.represented_players],
  )
}

#text(size: 8pt, weight: "bold")[Ranking artifact SHA-256]
#for artifact in data.artifact_hashes {
  text(size: 6pt, fill: muted)[#artifact.name  #artifact.sha256]
  linebreak()
}
#if data.source_files.len() > 0 [
  #v(5pt)
  #text(size: 8pt, weight: "bold")[Source CSV SHA-256]
  #for source in data.source_files {
    text(size: 6pt, fill: muted)[#source.name  #source.sha256]
    linebreak()
  }
]

#section("06 / LIMITATIONS", "Interpretation and responsible use")
The available data does not encode dew, boundary dimensions, field placements,
pitch deterioration, weather, or all tactical choices. Competition coverage
and player exposure are uneven; the pressure index and contextual baselines
are deterministic proxies, not causal estimates. Match context and role
changes can influence observed performance. Shrinkage and volatility penalties
reduce but do not eliminate sampling bias. The split-half stability gate is
not met (rho target >= 0.65); use these rankings as exploratory evidence, not
as a validated measure of future performance. The threshold is reported
unchanged.

#v(10pt)
#text(size: 7pt, fill: muted)[
Reproduction: `python -m clutch_x.report.build_report`. The report data JSON,
Typst source, and PDF are emitted together. The report builder validates rank
integrity before compiling and hashes the exact ranking artifacts used.
]
