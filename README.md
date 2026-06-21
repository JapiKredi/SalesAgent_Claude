<p align="center">
  <img src="banner.svg" alt="AI Sales Team for Claude Code" width="100%">
</p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/install-one--liner-blue?style=for-the-badge" alt="Install"></a>
  <a href="#commands"><img src="https://img.shields.io/badge/14_skills-ready-8b5cf6?style=for-the-badge" alt="14 Skills"></a>
  <a href="#how-it-works"><img src="https://img.shields.io/badge/5_parallel-agents-22c55e?style=for-the-badge" alt="5 Agents"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-gray?style=for-the-badge" alt="MIT License"></a>
</p>

> **Your AI-powered sales team, running inside Claude Code.**
> Research any company, qualify leads with BANT + MEDDIC, map the buying committee, generate personalized outreach, prepare for meetings, and produce professional PDF pipeline reports — all from the command line.

---

> **Fork notice.** This repository is a fork of [**ai-sales-team-claude**](https://github.com/zubair-trabzada/ai-sales-team-claude) by **Zubair Trabzada**, used and redistributed under the MIT License. It has been modified by **JapiKredi** — see [Credits & License](#credits--license). All credit for the original design and skills belongs to the original author.

---

## What This Does

Type a command in Claude Code and get instant, actionable sales intelligence:

```
> /sales prospect https://acme.com

Launching 5 parallel agents...
  ✓ Company Research & Firmographics    — Fit Score: 82/100
  ✓ Decision Maker Identification       — 4 contacts found
  ✓ Opportunity Assessment (BANT)       — Score: 78/100
  ✓ Competitive Intelligence            — 3 competitors mapped
  ✓ Outreach Strategy & Messaging       — 5-email sequence ready

┌─────────────────────────────────────────────────┐
│  PROSPECT SCORE                                 │
│                                                 │
│  ██████████████████████████████████░░░░  85/100  │
│                                                 │
│  Grade: A  —  Strong Prospect                   │
│  Action: Invest significant effort              │
└─────────────────────────────────────────────────┘

Full analysis saved to PROSPECT-ANALYSIS.md
```

---

## Quick Start

### One-Command Install

```bash
curl -fsSL https://raw.githubusercontent.com/JapiKredi/SalesAgent_Claude/main/install.sh | bash
```

### Manual Install

```bash
git clone https://github.com/JapiKredi/SalesAgent_Claude.git
cd SalesAgent_Claude
./install.sh
```

### Optional: PDF Reports & Enhanced Parsing

```bash
pip install -r requirements.txt
```

<details>
<summary><strong>What the installer does</strong></summary>

```
╔══════════════════════════════════════════════════════════╗
║  AI Sales Team — Claude Code Skills                     ║
║  14 Skills · 5 Agents · 4 Scripts · PDF                 ║
╚══════════════════════════════════════════════════════════╝

Installing skills...
  ✓ sales (orchestrator)
  ✓ sales-prospect
  ✓ sales-research
  ✓ sales-qualify
  ✓ sales-contacts
  ✓ sales-outreach
  ✓ sales-followup
  ✓ sales-prep
  ✓ sales-proposal
  ✓ sales-objections
  ✓ sales-icp
  ✓ sales-competitors
  ✓ sales-report
  ✓ sales-report-pdf

Installing agents...
  ✓ sales-company
  ✓ sales-contacts
  ✓ sales-opportunity
  ✓ sales-competitive
  ✓ sales-strategy

Installing scripts...
  ✓ analyze_prospect.py
  ✓ lead_scorer.py
  ✓ contact_finder.py
  ✓ generate_pdf_report.py

Installing templates...
  ✓ outreach-cold.md
  ✓ outreach-warm.md
  ✓ outreach-referral.md
  ✓ meeting-prep.md
  ✓ proposal-template.md
  ✓ objection-playbook.md
```

</details>

---

## Commands

| Command | Description | Output |
|:--------|:------------|:-------|
| `/sales prospect <url>` | Full prospect audit — **5 parallel agents** | `PROSPECT-ANALYSIS.md` |
| `/sales quick <url>` | 60-second prospect snapshot | Terminal output |
| `/sales research <url>` | Company research & firmographics | `COMPANY-RESEARCH.md` |
| `/sales qualify <url>` | BANT + MEDDIC lead scoring | `LEAD-QUALIFICATION.md` |
| `/sales contacts <url>` | Decision maker identification | `DECISION-MAKERS.md` |
| `/sales outreach <prospect>` | Cold outreach email sequence | `OUTREACH-SEQUENCE.md` |
| `/sales followup <prospect>` | Follow-up email sequence | `FOLLOWUP-SEQUENCE.md` |
| `/sales prep <url>` | Meeting preparation brief | `MEETING-PREP.md` |
| `/sales proposal <client>` | Client proposal generator | `CLIENT-PROPOSAL.md` |
| `/sales objections <topic>` | Objection handling playbook | `OBJECTION-PLAYBOOK.md` |
| `/sales icp <description>` | Ideal Customer Profile builder | `IDEAL-CUSTOMER-PROFILE.md` |
| `/sales competitors <url>` | Competitive intelligence | `COMPETITIVE-INTEL.md` |
| `/sales report` | Pipeline report (Markdown) | `SALES-REPORT.md` |
| `/sales report-pdf` | Pipeline report (PDF) | `SALES-REPORT-*.pdf` |

---

## Using `/sales prospect`

`/sales prospect` is the flagship command — it runs a full, scored audit of any company with 5 parallel agents and writes a ready-to-use `PROSPECT-ANALYSIS.md`.

### 1. Run it

Point it at the target company's URL (a bare name works too — the agents will search for it):

```
> /sales prospect https://www.ramp.com
```

> The hyphenated form `/sales-prospect https://www.ramp.com` also works — it calls the same skill directly, bypassing the orchestrator.

### 2. What happens (≈2–3 min)

| Phase | What it does |
|:------|:-------------|
| **1 — Discovery** | Fetches the homepage + key subpages, detects company type & industry, extracts structured data |
| **2 — Parallel analysis** | Launches 5 agents at once: Company Fit, Contact Access, Opportunity (BANT/MEDDIC), Competitive Position, Outreach Readiness |
| **3 — Synthesis** | Aggregates into a weighted 0–100 score + grade, an action plan, and a copy-paste-ready first email |

### 3. What you get

- A scored **`PROSPECT-ANALYSIS.md`** in the current directory
- A condensed scorecard printed to the terminal
- A ready-to-send first outreach email with two subject-line options

### 💡 Tip — ground the score in *your* offer

By default the analysis assumes a generic seller, so the fit-related scores come back "conditional." For a sharp, accurate result, tell Claude what **you** sell in the same message — e.g.:

```
> /sales prospect https://www.ramp.com — I sell Gong (revenue intelligence for B2B sales teams)
```

Claude threads your product/ICP through all 5 agents, so **Company Fit**, **Competitive Position**, and **Outreach Readiness** reflect *your* deal instead of a generic one.

> **Requires:** Claude Code with web access. No cookie or API key needed — the analysis runs entirely on publicly available information.

---

## How It Works

### Architecture

The system uses a three-layer architecture — one orchestrator skill routes commands to 13 sub-skills, with the flagship `/sales prospect` command launching 5 specialized agents in parallel:

```
                         ┌──────────────────────────┐
                         │     /sales prospect       │
                         │      (Orchestrator)       │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                  ▼
          ┌─────────────┐   ┌─────────────────┐   ┌──────────────┐
          │   PHASE 1    │   │     PHASE 2      │   │   PHASE 3    │
          │  Discovery   │   │ Parallel Analysis │   │  Synthesis   │
          └──────┬──────┘   └────────┬──────────┘   └──────┬───────┘
                 │                   │                      │
                 ▼                   ▼                      ▼
          ┌─────────────┐   ┌───────────────┐       ┌──────────────┐
          │ Fetch site   │   │ 5 agents run  │       │ Aggregate    │
          │ Extract data │   │ simultaneously│       │ Score (0-100)│
          │ Detect type  │   │               │       │ Action plan  │
          │ Run scripts  │   │               │       │ First email  │
          └─────────────┘   └───────┬───────┘       └──────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                   │
        ┌────────────────┐  ┌──────────────┐  ┌───────────────┐
        │ ┌────────────┐ │  │ ┌──────────┐ │  │ ┌───────────┐ │
        │ │  Company   │ │  │ │ Contacts │ │  │ │Opportunity│ │
        │ │  Research  │ │  │ │  Finder  │ │  │ │  Scoring  │ │
        │ │            │ │  │ │          │ │  │ │           │ │
        │ │ Fit: 25%   │ │  │ │Access:20%│ │  │ │Quality:20%│ │
        │ └────────────┘ │  │ └──────────┘ │  │ └───────────┘ │
        └────────────────┘  └──────────────┘  └───────────────┘
        ┌────────────────┐  ┌──────────────┐
        │ ┌────────────┐ │  │ ┌──────────┐ │
        │ │Competitive │ │  │ │ Outreach │ │
        │ │  Analysis  │ │  │ │ Strategy │ │
        │ │            │ │  │ │          │ │
        │ │Position:15%│ │  │ │Ready: 20%│ │
        │ └────────────┘ │  │ └──────────┘ │
        └────────────────┘  └──────────────┘
```

### Cross-Skill Integration

Skills automatically detect and build on each other's output:

```
/sales prospect  ──►  PROSPECT-ANALYSIS.md
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                     ▼
/sales outreach      /sales prep           /sales proposal
 (uses contacts,     (uses all prior       (uses qualification,
  research data)      analysis data)        competitive intel)
       │                    │                     │
       ▼                    ▼                     ▼
  OUTREACH-              MEETING-              CLIENT-
  SEQUENCE.md            PREP.md               PROPOSAL.md
```

---

## Prospect Scoring

Every prospect gets a **weighted composite score (0-100)** calculated from 5 dimensions:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   PROSPECT SCORE FORMULA                                            │
│                                                                     │
│   Company Fit ............ 25%   ████████████░░░░░░░░  Size,        │
│                                                        industry,    │
│                                                        growth       │
│                                                                     │
│   Contact Access ......... 20%   █████████░░░░░░░░░░░  Decision     │
│                                                        makers,      │
│                                                        warm paths   │
│                                                                     │
│   Opportunity Quality .... 20%   █████████░░░░░░░░░░░  BANT score,  │
│                                                        pain points  │
│                                                                     │
│   Competitive Position ... 15%   ███████░░░░░░░░░░░░░  Current      │
│                                                        solutions,   │
│                                                        switching    │
│                                                                     │
│   Outreach Readiness ..... 20%   █████████░░░░░░░░░░░  Channels,    │
│                                                        messaging,   │
│                                                        anchors      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Grade Interpretation

```
  Score    Grade    Action
 ───────────────────────────────────────────────────────────
  90-100    A+      🔥  Hot Lead — prioritize immediately
  75-89     A       ✅  Strong Prospect — invest significant effort
  60-74     B       📊  Qualified Lead — pursue with standard approach
  40-59     C       🔄  Lukewarm — nurture, don't hard sell
   0-39     D       ⏸️   Poor Fit — deprioritize or disqualify
```

### Qualification Frameworks

<details>
<summary><strong>BANT Scoring (0-100)</strong></summary>

Each dimension scored 0-25 from publicly available signals:

| Dimension | Max | Signals |
|-----------|-----|---------|
| **Budget** | 25 | Funding, employee count, pricing pages, tech spend |
| **Authority** | 25 | Decision makers found, C-suite identified, org chart |
| **Need** | 25 | Pain points, job posts, reviews, competitor gaps |
| **Timeline** | 25 | Recent funding, hiring, contract cycles, urgency |

</details>

<details>
<summary><strong>MEDDIC Assessment (0-100%)</strong></summary>

Each dimension assessed for completeness:

- **M**etrics — Can we quantify the business impact?
- **E**conomic Buyer — Who controls the budget?
- **D**ecision Criteria — How will they evaluate solutions?
- **D**ecision Process — What's their buying process?
- **I**dentify Pain — Are pain points confirmed?
- **C**hampion — Is there an internal advocate?

</details>

---

## Examples

### Full Prospect Audit

```
> /sales prospect https://stripe.com

Phase 1: Discovering company information...
  ✓ Homepage fetched — SaaS / Fintech detected
  ✓ 6 subpages extracted (about, team, pricing, careers, blog, contact)
  ✓ analyze_prospect.py — 23 data points extracted

Phase 2: Running parallel analysis (5 agents)...
  ✓ Company Research      — Fit Score: 88/100
  ✓ Contact Discovery     — 6 decision makers found
  ✓ Opportunity Scoring   — BANT: 82/100
  ✓ Competitive Intel     — 4 competitors mapped
  ✓ Outreach Strategy     — 5-email sequence drafted

Phase 3: Synthesizing results...
  ✓ Prospect Score: 85/100 (Grade A)
  ✓ Top contact: [CTO] — strong technical champion signal
  ✓ Opening angle: recent Series D + engineering hiring surge

Output: PROSPECT-ANALYSIS.md
```

### Lead Qualification

```
> /sales qualify https://notion.so

Analyzing notion.so for lead qualification...

  BANT Score: 78/100 (Grade A)
  ┌────────────────────────────────────┐
  │ Budget:    ██████████████████░░ 22  │
  │ Authority: ████████████████░░░░ 18  │
  │ Need:      ██████████████████░░ 20  │
  │ Timeline:  ████████████████░░░░ 18  │
  └────────────────────────────────────┘
  MEDDIC Completeness: 72%

Action: Schedule discovery call — high-priority prospect.
Output: LEAD-QUALIFICATION.md
```

### Outreach Generation

```
> /sales outreach "Linear"

Generating outreach sequence for Linear...
  Type: Cold outreach (5-email sequence)
  Framework: Observation → Connection → Ask
  Personalized for: Engineering-focused B2B SaaS

  Email 1: "Quick question about [specific pain point]"    Day 1
  Email 2: "Saw your team's post about [trigger event]"    Day 3
  Email 3: "[Mutual connection] suggested I reach out"     Day 7
  Email 4: "3 ideas for [specific challenge]"              Day 14
  Email 5: "Should I close the file?"                      Day 21

Output: OUTREACH-SEQUENCE.md
```

### Meeting Prep

```
> /sales prep https://datadog.com

Generating meeting brief for datadog.com...
  ┌────────────────────────────────────────────┐
  │  MEETING PREP BRIEF                        │
  │                                            │
  │  Company:       Datadog                    │
  │  Attendees:     3 profiled                 │
  │  Talking Points: 7 prepared                │
  │  Discovery Qs:  10 ready                   │
  │  Objections:    5 with responses           │
  │  Cheat Sheet:   1 page                     │
  └────────────────────────────────────────────┘

Output: MEETING-PREP.md
```

---

## Project Structure

```
SalesAgent_Claude/
│
├── sales/SKILL.md                     ← Main orchestrator (routes all /sales commands)
│
├── skills/                            ← 13 sub-skills
│   ├── sales-prospect/SKILL.md           Full prospect audit (launches 5 agents)
│   ├── sales-research/SKILL.md           Company research & firmographics
│   ├── sales-qualify/SKILL.md            Lead qualification (BANT + MEDDIC)
│   ├── sales-contacts/SKILL.md           Decision maker identification
│   ├── sales-outreach/SKILL.md           Cold outreach email sequences
│   ├── sales-followup/SKILL.md           Follow-up email generation
│   ├── sales-prep/SKILL.md               Meeting preparation brief
│   ├── sales-proposal/SKILL.md           Client proposal generator
│   ├── sales-objections/SKILL.md         Objection handling playbook
│   ├── sales-icp/SKILL.md                Ideal Customer Profile builder
│   ├── sales-competitors/SKILL.md        Competitive intelligence
│   ├── sales-report/SKILL.md             Pipeline report (Markdown)
│   └── sales-report-pdf/SKILL.md         Pipeline report (PDF)
│
├── agents/                            ← 5 parallel subagents
│   ├── sales-company.md                  Company fit & firmographics (25%)
│   ├── sales-contacts.md                 Decision maker mapping (20%)
│   ├── sales-opportunity.md              Opportunity & BANT scoring (20%)
│   ├── sales-competitive.md              Competitive positioning (15%)
│   └── sales-strategy.md                 Outreach strategy & messaging (20%)
│
├── scripts/                           ← Python utilities
│   ├── analyze_prospect.py               Website scraping & data extraction
│   ├── lead_scorer.py                    BANT/MEDDIC scoring engine
│   ├── contact_finder.py                 Team & leadership extraction
│   └── generate_pdf_report.py            ReportLab PDF generator
│
├── templates/                         ← Output templates
│   ├── outreach-cold.md                  5-email cold sequence
│   ├── outreach-warm.md                  3-email warm intro sequence
│   ├── outreach-referral.md              3-email referral sequence
│   ├── meeting-prep.md                   Meeting prep brief
│   ├── proposal-template.md              11-section client proposal
│   └── objection-playbook.md             15 universal objections
│
├── install.sh                         ← One-command installer
├── uninstall.sh                       ← Cleanup script
├── requirements.txt                   ← Python deps (reportlab, bs4, requests)
└── LICENSE                            ← MIT
```

---

## Use Cases

<table>
<tr>
<td width="33%">

### Founders & Solopreneurs

```bash
# Full prospect intelligence
/sales prospect https://target.com

# Ready-to-send email sequence
/sales outreach "Target Company"

# Prep before the call
/sales prep https://target.com
```

</td>
<td width="33%">

### Sales Teams

```bash
# Qualify inbound leads
/sales qualify https://lead.com

# Map the buying committee
/sales contacts https://lead.com

# Handle pricing objections
/sales objections "enterprise SaaS"
```

</td>
<td width="33%">

### Agency Owners

```bash
# Client proposal with pricing
/sales proposal "Client Name"

# Competitive positioning
/sales competitors https://client.com

# Define ideal customer
/sales icp "B2B SaaS, 50-200 emp"
```

</td>
</tr>
</table>

---

## Requirements

| Requirement | Status | Notes |
|:------------|:------:|:------|
| **Claude Code** | Required | [Install Claude Code](https://docs.anthropic.com/en/docs/claude-code) |
| **Python 3.8+** | Optional | For scripts and PDF generation |
| **reportlab** | Optional | `pip install reportlab` — PDF reports |
| **beautifulsoup4** | Optional | `pip install beautifulsoup4` — enhanced parsing |
| **requests** | Optional | `pip install requests` — fallback URL fetching |

---

## Uninstall

```bash
# From the repo directory
./uninstall.sh

# Or remotely
curl -fsSL https://raw.githubusercontent.com/JapiKredi/SalesAgent_Claude/main/uninstall.sh | bash
```

Removes all skills, agents, scripts, and templates from `~/.claude/`. Python packages are not removed.

---

## Credits & License

- **Original project:** [ai-sales-team-claude](https://github.com/zubair-trabzada/ai-sales-team-claude) by **Zubair Trabzada** — © Zubair Trabzada, MIT License.
- **This fork:** modifications © 2026 JapiKredi, released under the same MIT License.

This is a derivative work distributed under the MIT License. The original copyright notice is retained in [LICENSE](LICENSE) as the license requires. See [LICENSE](LICENSE) for full terms.

---

<p align="center">
  <strong>MIT License</strong> · © Zubair Trabzada · Modifications © 2026 JapiKredi
  <br>
  Forked from <a href="https://github.com/zubair-trabzada/ai-sales-team-claude">ai-sales-team-claude</a>
  <br><br>
  <a href="https://github.com/JapiKredi/SalesAgent_Claude/issues">Report Bug</a> ·
  <a href="https://github.com/JapiKredi/SalesAgent_Claude/issues">Request Feature</a>
</p>
