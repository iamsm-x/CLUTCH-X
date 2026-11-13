# **Product Requirements Document (PRD): CLUTCH-X** 

**Product Name:** CLUTCH-X ( _Contextual Leverage & Under-Pressure T20 Execution Engine_ ) **Version:** 1.0 

**Domain:** T20 Cricket Sports Analytics (IPL & T20 Internationals, 2022–Present) **Primary Deliverables:** Ranked Top 10 Pressure Batters, Ranked Top 10 Pressure Bowlers, and Reproducible Analytical Report 

## **1. Executive Overview & Problem Statement** 

Standard T20 aggregates—such as overall batting strike rate or bowling economy—treat every delivery equally, masking how players perform when match leverage peaks. A boundary hit when chasing 14 runs per over with 3 wickets in hand carries vastly different competitive weight than a boundary hit in a low-stakes middle over. 

**CLUTCH-X** is a delivery-level sports analytics engine designed to quantify match pressure on every ball, benchmark player execution under high pressure against their normal baseline performance, and rank the most statistically reliable pressure performers across batting and bowling disciplines. 

## **2. Product Goals & Non-Goals** 

### **Primary Goals** 

- **Quantify Delivery-Level Pressure:** Build a transparent, mathematical Pressure Index ( 𝑃𝐼  ) that separates high-leverage game states from ordinary play across both 1st and 2nd innings. 

- **Measure Baseline-Adjusted Clutch Impact:** Evaluate how each batter and bowler performs under pressure relative to both their own normal-situation baseline and par expectations for that match context. 

- **Ensure Statistical Fairness & Reliability:** Control for sample-size noise, match-to-match variance, and scoring environment differences between IPL and T20I competitions (2022 onwards). 

- **Deliver Auditable Rankings & Diagnostics:** Produce two strictly ordered, non-duplicate Top-10 lists (Batters and Bowlers) supported by reproducible tables and visual evidence. 

### **Non-Goals (Out of Scope)** 

- Analysis of pre-2022 historical data or non-T20 formats (ODIs, Test cricket). 

- Subjective player rankings driven by reputation or highlight reels without empirical backing in the supplied dataset. 

- Real-time live ball-by-ball streaming ingestion (system operates on batch historical CSV datasets). 

## **3. Target Users & Personas** 

|**User Persona**|**Core Pain Point**|**Primary Decision**<br>**Supported**|**Key Metrics**<br>**Consumed**|
|---|---|---|---|
|**Auction Scouts &**<br>**Recruitment**<br>**Teams**|High-profile players<br>often carry inflated<br>auction prices<br>based on<br>low-leverage<br>stat-padding, while<br>true clutch finishers<br>go undervalued.|Identifying<br>undervalued<br>middle-order<br>finishers, crisis<br>anchors, and<br>death-over<br>specialists ahead of<br>player auctions.|Clutch Rating Index,<br>Pressure vs.<br>Baseline Delta,<br>Sample Volume.|
|**Performance**<br>**Analysts & Data**<br>**Scientists**|Raw ball-by-ball<br>CSVs lack<br>pre-computed<br>match states, and<br>naive Required Run<br>Rate filters ignore<br>1st-innings<br>pressure.|Building<br>reproducible,<br>bias-free player<br>evaluation models<br>across IPL and T20I<br>datasets.|Pressure Index (  )<br>𝑃𝐼<br>Distribution, Runs<br>Above Expected,<br>Variance/Consisten<br>cy Score.|
|**Head Coaches &**<br>**Team Captains**|Tactical matchups<br>often rely on gut<br>feel rather than<br>objective evidence<br>of who executes<br>under scoreboard<br>or collapse<br>pressure.|Promoting batters<br>during early<br>collapses,<br>deploying Impact<br>Players, and<br>assigning overs<br>17–20 in tight<br>games.|Phase-Specific<br>Pressure<br>SR/Economy, Dot<br>Ball %, Boundary<br>Retention %.|
|**Franchise &**<br>**National Selectors**|Players who<br>dominate bilateral<br>leagues sometimes<br>falter in knockout<br>games or<br>high-stakes<br>international<br>chases.|Finalizing Playing<br>XIs and tournament<br>squads with proven<br>cross-match<br>reliability.|Knockout Multiplier<br>Impact,<br>Match-Level<br>Positive Impact<br>Rate (%).|



**4. User Stories & Acceptance Criteria Epic 1: Context & Pressure Modeling** 

- **US-1.1 (Performance Analyst):** As a Performance Analyst, I want the engine to reconstruct the exact pre-delivery scoreboard state (score, wickets lost, balls remaining, target, and tournament stage) for every row in ball_by_ball.csv, so that pressure is measured accurately before each ball is bowled. 

- **Acceptance Criteria:** 100% of legal deliveries in valid  1st and 2nd innings have accurate cumulative pre-delivery runs, wickets, and balls remaining; rain-curtailed matches adjust targets using revised_target and revised overs. 

- **US-1.2 (Data Scientist):** As a Data Scientist, I want a unified Pressure Index (  –  0  100  ) that captures both 2nd-innings chase tension and 1st-innings collapse/death-over urgency, so that 1st-innings specialists are not unfairly excluded. 

- **Acceptance Criteria:** High-pressure classification (  𝑃𝐼 ≥ 𝑡ℎ𝑟𝑒𝑠ℎ𝑜𝑙𝑑  ) captures 15%–25% of total deliveries and exhibits statistically distinct scoring/wicket rates compared to normal deliveries. 

### **Epic 2: Fair Benchmarking & Clutch Scoring** 

- **US-2.1 (Auction Scout):** As an Auction Scout, I want  player performance normalized across IPL and T20I scoring environments from 2022 onward, so I can compare domestic franchise performers and international players on an equal footing. 

- **Acceptance Criteria:** Every delivery is benchmarked  against context-expected runs and wicket probabilities grouped by (match_format, season, innings, over_phase). 

- **US-2.2 (Franchise Selector):** As a Franchise Selector,  I want players filtered by minimum high-pressure ball thresholds and penalized for erratic match-to-match variance, so a single lucky cameo cannot vault a player into the Top 10. 

- **Acceptance Criteria:** Eligibility cutoffs enforce minimum  high-pressure balls faced/bowled across multiple matches, and final ratings incorporate cross-match consistency. 

### **Epic 3: Tactical Diagnostics & Reporting** 

- **US-3.1 (Head Coach):** As a Head Coach, I want side-by-side  comparisons of each Top-10 player's normal baseline vs. high-pressure execution, so I know whether a player elevates their game or simply maintains elite output under stress. 

- **Acceptance Criteria:** Output tables and quadrant scatter  plots display Baseline Rating, High-Pressure Rating, and Net Clutch Delta for every ranked player. 

## **5. Core Feature Specifications** 

### **Feature 1: Data Ingestion & Live State Reconstruction Pipeline** 

- **Relational Schema Integration:** Joins ball_by_ball.csv  with matches.csv (match_id), competitions.csv (comp_id), playing_eleven.csv, teams.csv, and 

   - competition_team_player_mapping.csv to bind delivery events to player metadata, 

   - competition format (IPL vs. T20I), and knockout status. 

- **Data Hygiene & Edge Cases:** 

- Excludes Super Overs (innings > 2) and abandoned matches with insufficient play. 

- Distinguishes legal deliveries from Wides/No-Balls when computing balls_remaining. 

- Incorporates DLS adjustments (first_inn_revised_overs, second_inn_revised_overs, 

### revised_target) so chase pressure remains accurate in rain-affected games. **Feature 2: Dynamic Ball-by-Ball Pressure Engine (  )** 𝑃𝐼 

Assigns a continuous score from  to  0 100  to every delivery using a weighted multi-factor 

formula: 

1. **2nd-Innings Chase Leverage:** 

- _Required Run Rate Ratio:_ 𝑅𝑅𝑅 / 𝑃𝑎𝑟𝑅𝑢𝑛𝑅𝑎𝑡𝑒  (scales nonlinearly as RRR exceeds  10 . 0 + ). 

- _Resource Scarcity Index:_ Interaction between wickets_lost  and balls_remaining (inspired by Duckworth-Lewis-Stern resource curves). 

2. **1st-Innings Setting Leverage:** 

- _Collapse Recovery Factor:_ Triggered when early wickets fall rapidly (e.g., ≥ 3  wickets inside overs 1–8, or ≥ 5  wickets before over 14). 

- _Death-Over Acceleration Factor:_ Overs 16–20 where  marginal runs heavily swing win probability. 

3. **Match Stakes Multiplier:** 

- Applies a contextual weight boost (e.g.,  1 . 15 × ) for knockout/playoff fixtures (knock_out == 1). 

4. **Regime Classification:** 

- Partitions deliveries into **Normal Pressure** (  𝑃𝐼 < 60  ) and **High Pressure** (  𝑃𝐼 ≥ 60  ) to enable clean baseline-vs.-clutch splits. 

### **Feature 3: Competition & Era Normalization (Baseline Benchmarking)** 

- **Contextual Expected Value Model:** Calculates baseline  expected_runs and expected_wicket_prob for every (match_format, season, innings, over_phase) bucket. This prevents high-scoring IPL seasons (e.g., 2024) from inflating ratings over lower-scoring T20I matches. 

- **Personal Player Baseline:** Computes each player's personal  performance profile on **Normal Pressure** deliveries (  𝑃𝐼 < 60  ) to establish their individual "usual performance level". 

### **Feature 4: Dual-Discipline Clutch Scoring (Batting & Bowling)** 

- **Batting Clutch Score (** 𝐵𝐶𝑆 **):** 

- **Pressure Runs Above Expected (pRAE):** ( 𝐴𝑐𝑡𝑢𝑎𝑙𝑅𝑢𝑛𝑠 − 𝐸𝑥𝑝𝑒𝑐𝑡𝑒𝑑𝑅𝑢𝑛𝑠 ) per 100 high-pressure balls faced. 

- **Baseline Strike Rate Delta (** ∆ 𝑆𝑅  𝑆 𝑅 **):** 𝑝𝑟𝑒𝑠𝑠𝑢𝑟𝑒 − 𝑆 𝑅  𝑛𝑜𝑟𝑚𝑎𝑙 

- **Boundary Retention & Dot Avoidance:** Tracks boundary  percentage and dot-ball percentage under pressure relative to normal play. 

- **Wicket Preservation:** Balls per dismissal under pressure  (penalizing reckless dismissals during chases/collapses). 

- **Bowling Clutch Score (** 𝐵𝑜𝐶𝑆 **):** 

- **Pressure Runs Saved Above Expected (pRSAE):** 

   - ( 𝐸𝑥𝑝𝑒𝑐𝑡𝑒𝑑𝑅𝑢𝑛𝑠 − 𝐴𝑐𝑡𝑢𝑎𝑙𝑅𝑢𝑛𝑠𝐶𝑜𝑛𝑐𝑒𝑑𝑒𝑑 ) 

   - per over under pressure. 

- **Baseline Economy Delta (** ∆ 𝐸𝑐𝑜𝑛  𝐸𝑐𝑜 𝑛 **):** 𝑛𝑜𝑟𝑚𝑎𝑙 − 𝐸𝑐𝑜 𝑛  𝑝𝑟𝑒𝑠𝑠𝑢𝑟𝑒  . 

- **Pressure Dot-Ball %:** Proportion of high-pressure deliveries  resulting in zero runs. 

- **Clutch Wicket Impact:** Wickets per 24 high-pressure balls, weighted higher for dismissing top/middle-order batters (batting_order 1–6). 

- **Reliability & Sample-Size Guardrails:** 

- Enforces minimum volume thresholds (e.g., ≥ 150  high-pressure balls faced/bowled across ≥ 10  matches). 

- Applies **Bayesian Shrinkage** toward the peer mean for  lower-volume qualifiers and subtracts a **Cross-Match Volatility Penalty** ( µ −λσ ) so consistent performers outrank volatile outliers. 

### **Feature 5: Auditable Top-10 Ranking & Visual Diagnostics** 

- **Leaderboard Export:** Outputs strictly ordered Rank  1–10 Batters and Rank 1–10 Bowlers with zero duplicate entries, mapped cleanly to player IDs/names for Unstop submission. 

- **Diagnostic Visualizations:** 

- _Pressure Index Distribution Histogram:_ Validates the  separation between ordinary deliveries and high-pressure moments. 

- _2x2 Quadrant Scatter Plot (Normal Rating vs. Pressure Rating):_ Visually separates "All-Weather Elites" and "Clutch Elevators" from "Flat-Track Bullies". 

- _Match-by-Match Consistency Chart:_ Box/strip plots  demonstrating repeatable impact across high-pressure appearances. 

## **6. Non-Functional & Compliance Requirements** 

- **Transparency & Reproducibility:** All formulas, feature  weights, normalization buckets, and cutoff thresholds must be explicitly documented and deterministic so any third-party analyst can reproduce the exact rankings from the raw CSVs. 

- **Parity Across Deliverables:** The rank order (1 to 10)  in the final report tables must match the Unstop dropdown selections 100%. 

- **Honest Model Limitations:** The system documentation  must explicitly outline analytical blind spots—such as the absence of dew indicators, boundary dimensions, field placements, and pitch deterioration metrics. 

## **7. Success Metrics (KPIs)** 

|**Category**|**Metric Name**|**Target / Definition**|
|---|---|---|
|**Analytical Validity**|**Pressure Regime**<br>**Separation**|High-pressure deliveries (<br>) show a<br>𝑃𝐼 ≥ 60<br>statistically significant (<br>) shift in wicket<br>𝑝 < 0 . 01<br>probability and scoring<br>variance vs. normal<br>deliveries.|
|**Statistical Reliability**|**Split-Half Rank Stability**|Spearman rank correlation (|



|||) when splitting<br>ρ ≥ 0 . 65<br>each eligible player's<br>high-pressure appearances<br>into odd vs. even matches.|
|---|---|---|
|**Fairness & Bias Control**|**Format & Innings Balance**|Top-10 lists naturally<br>represent both IPL and T20I<br>contributors as well as both<br>1st-innings and 2nd-innings<br>pressure situations without<br>artificial hardcoding.|
|**Domain Discovery**|**Data-Over-Reputation**<br>**Signal**|At least 2–3 underrated<br>specialists (e.g.,<br>middle-order finishers or<br>tactical death bowlers)<br>statistically outrank<br>higher-profile superstars<br>based on baseline delta and<br>consistency.|
|**Submission Compliance**|**100% Auditability & Parity**|Zero duplicate players,<br>100% match between<br>report rankings and Unstop<br>dropdown fields, and full<br>documentation of code<br>logic and limitations.|



