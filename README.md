# NBA Analytics Challenge
### Aberdeen Advisors Intern Program — Aberdeen Angels Scenario

![Aberdeen Angels Team](assets/team.png)

You're an analytics consultant hired by the **Aberdeen Angels**, a fictional NBA team on the edge of title contention. The General Managers have $30 million to spend and need one more player before the trade deadline. Your job: dig through real player data, build a dashboard, and deliver a data-backed recommendation they can act on.

---

## What's in This Repo

| File | What it is |
|------|-----------|
| `NBA Analytics Packet.html` | The full assignment guide — open this in your browser to get started |
| `Mock-Dashboard-Reference.html` | A reference mockup of the Power BI dashboard you'll build |
| `nba_data_raw.xlsx` | The raw NBA player dataset (430+ players, 2024–25 season) |

---

## The 8 Phases

Work through the phases in order. Each one ends with a gate check before you move on.

| # | Phase | What you do |
|---|-------|-------------|
| 1 | **Understand the Goal** | Write a paragraph restating the GM's question in your own words and forming a hypothesis |
| 2 | **Review the Dataset** | Explore the data, identify key columns, and note anything surprising |
| 3 | **Clean the Data** | Find and fix 4 hidden data problems — log every issue before you touch it |
| 4 | **Pick Your KPIs** | Choose 3–4 stats that directly answer "who gives the most wins per dollar?" |
| 5 | **Find Your Top 3** | Apply the GM's filters, rank by Bang for Buck, and identify your best candidates |
| 6 | **Build the Dashboard** | Create a 3-tab Power BI dashboard modeled on the reference mockup |
| 7 | **Write Your Insights** | Translate your findings into a concise executive write-up |
| 8 | **Present to the Partners** | Deliver a 3-slide presentation with one clear recommendation |

---

## The GM's Criteria

Every player you consider must meet all three requirements:

- Salary **under $30 million**
- In **years 3–5** of their NBA career (`contract_year_number` column)
- Played in **at least 40 games** this season (`games_played` column)

---

## Key Metric: Bang for Buck

The most important stat in this analysis is **Win Shares per $10M** (`win_shares_per_10m`) — for every $10 million spent, how many wins does the player contribute? This directly answers the GM's question and is already calculated in the dataset.

```
Bang for Buck = win_shares ÷ (salary_millions ÷ 10)
```

A score above 1.5 is good. Above 2.5 is great.

---

## What You'll Produce

By the end of the assignment you'll have:

- A cleaned Excel dataset with every data issue documented in a Cleaning Log
- A 3-tab Power BI dashboard the GM can actually use
- A 3-slide presentation with one specific player recommendation

---

## Ground Rules

1. **Back it up with numbers.** "I think Player X is good" doesn't cut it — show the data.
2. **Log before you fix.** In Phase 3, every data issue must be written down *before* you change anything.
3. **One clear answer.** Your final presentation ends with one player. Not three options — one recommendation, backed by your analysis.

---

## File Naming Convention

Name every deliverable: `YYYY-MM-DD_YourName_Deliverable_v1.ext`

Example: `2024-07-15_JSmith_Cleaning-Template_v1.xlsx`

If you revise after feedback, increment the version number (v2, v3). Never overwrite a previous version.

---

*Aberdeen Advisors Intern Program 2024 · Aberdeen Angels Scenario*
