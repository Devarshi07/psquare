# P Square — Predict & Prevent
### v1.1: Heart Health + Biological Age Edition — A Hyper-Personalized Cardiovascular & Longevity Agent on WhatsApp

> **Mission:** Tell every user their *true* heart health and *true* biological age today, predict their cardiovascular risk for the next 10 years, and give them a *personal* (not generic) plan to reverse it — delivered as a friendly WhatsApp conversation plus a beautiful PDF report.

---

## 0. How To Use This Document (Read Me First, Claude)

You are Claude Code working on the **P Square** repository. This file is your single source of truth for v1.1.

**Hard rules — never break these:**
1. **v1.1 scope = Heart Health + PPG + Biological Age. Nothing else.** Do not build PCOS, diabetes, weight management, full diet engine, or other modules. They are roadmap items (§16). Architect the code so they slot in cleanly, but do not implement them now.
2. **Personalization is the product.** No two users should ever receive the same plan. Every recommendation must reference at least 3 specific data points from the user's profile (e.g., *"because your LDL is 142, your father had a heart attack at 52, and you walk fewer than 4,000 steps/day"*).
3. **Medical safety overrides everything.** P Square is a *wellness and prevention* platform — never a diagnostic tool. Never claim to diagnose, treat, or cure. Always escalate red flags (chest pain, breathlessness at rest, syncope, BP > 180/120, suspected stroke) to "call 112 / consult a cardiologist now".
4. **No hallucinated medical facts.** Risk thresholds, reference ranges, scoring formulas, and biological-age calculations live in `medical_knowledge/` as hard-coded, cited Python — never improvised by the LLM at runtime.
5. **Keep questionnaires short.** Onboarding ≤ 12 questions. Biological-age questionnaire ≤ 5 questions. Pre-PPG check ≤ 3 questions. **Long forms kill completion** — use WhatsApp interactive buttons/lists wherever possible, never free-text where a button works.
6. **Ask before assuming.** If a spec is ambiguous, stop and ask the human.

---

## 1. Product Overview (v1.1)

**Name:** P Square (P² = Predict × Prevent)
**v1.1 scope:** Heart Health + PPG (camera-based vitals) + Biological Age
**Channel:** WhatsApp (primary), with PDF report delivery. PPG and FaceAge use a short-lived web mini-app for camera access (see §11).
**Core promise:** *"In 10 minutes I'll show you your true heart age, your biological age, and a plan that's actually yours."*

### 1.1 The four centerpieces

#### 🎯 The P² Heart Score (Dial, 0–100)
A single composite score that tells the user how healthy their heart is, *right now*. Higher is better.
- **85–100 — Excellent** (green)
- **70–84 — Good** (light green)
- **55–69 — Fair** (amber)
- **40–54 — At Risk** (orange)
- **0–39 — High Risk** (red)

Rendered as a half-circle gauge in the PDF and as an image in WhatsApp. Score changes over time are tracked and shown as a trend line.

**Composition (deterministic formula, see §7):**
- 35% — 10-year cardiovascular risk (inverted; lower CV risk = more points). Computed via **QRISK3** (preferred) with **Framingham** as fallback.
- 15% — Heart Age vs Chronological Age gap.
- 25% — Modifiable lifestyle factors (BP, lipid status, smoking, activity, diet, sleep, stress, alcohol, BMI/waist).
- 15% — Known cardiovascular conditions and family history modifiers.
- **10% — PPG-derived signals (HR, HRV, stress index)** when available; auto-redistributed if user hasn't done a PPG scan yet.

#### 📊 The Heart Scoreboard (multi-metric panel)
A WhatsApp message and PDF section showing each pillar separately. The user sees *why* their score is what it is.

| Pillar | Metric(s) | Status bands |
|---|---|---|
| **10-Yr CV Risk** | QRISK3 or Framingham % | <5% Low · 5–10 Borderline · 10–20 Moderate · ≥20 High |
| **Heart Age** | Computed heart age − chronological age | Younger / On par / Older by N years |
| **Blood Pressure** | Avg systolic/diastolic over last 7 days | Optimal · Normal · Elevated · Stage 1 · Stage 2 |
| **Cholesterol** | LDL, HDL, Triglycerides, Total/HDL ratio | Per ACC/AHA + ICMR Indian thresholds |
| **Resting Heart Rate** | Manual or PPG-derived | Athletic · Excellent · Good · Average · Poor |
| **HRV (PPG)** | RMSSD, ms | Personal baseline + age-adjusted band |
| **Stress / Fatigue (PPG)** | Composite index 0–100 | Low · Moderate · High |
| **Activity** | Daily steps avg + active minutes | <5k · 5–7.5k · 7.5–10k · 10k+ |
| **BMI / Waist** | BMI + waist (Indian thresholds) | Healthy · Overweight · Obese |
| **Lifestyle Vitals** | Smoking, alcohol, sleep hrs, stress 1–10 | Per category |

Each pillar gets a color band, a one-line plain-English explanation, and the **single highest-impact action** to improve it.

#### 📷 PPG Vitals Scan (Photoplethysmography — NEW)
30-second finger-on-camera scan that returns **Heart Rate, Heart Rate Variability (HRV), and a Stress / Fatigue Index**. Works through a short-lived web mini-app the bot links to. Detailed spec in §10.

#### 🧬 Biological Age (NEW)
Estimated from **5 short questions + a face selfie**. Returns a single number (e.g., "Your biological age: 38 — that's 4 years older than your real age of 34") plus the top 3 visible/lifestyle drivers and a 60-day reversal plan. Detailed spec in §11.

### 1.2 v1.1 Feature List
1. **Onboarding** — heart-focused intake (~4 min, max 12 Qs)
2. **Heart Score Dial** — 0–100 with color bands
3. **Heart Scoreboard** — pillar-by-pillar breakdown
4. **10-Year CV Risk Calculator** — QRISK3 + Framingham fallback
5. **Heart Age Estimator**
6. **PPG Vitals Scan** — HR, HRV, Stress/Fatigue Index via finger on camera (web mini-app)
7. **Biological Age Module** — 5 Qs + face selfie → bio age + reversal plan
8. **BP Logging** — text or photo of BP monitor
9. **Resting Heart Rate Logging** — morning check-in or PPG
10. **Steps Tracking** — manual or screenshot of fitness app
11. **Daily Heart Habits Checklist** — 6 yes/no actions per day
12. **Personalized Cardio + Strength Plan** — equipment-, time-, condition-aware
13. **Heart-Healthy Meal Suggestions** — on-demand "what should I eat" answers
14. **Stress & HRV Micro-Practice** — daily 5-min protocol picked for the user
15. **Smoker's Reduction Protocol** — only if user smokes
16. **Lab Cadence Recommender** — when to next get lipid panel / ECG / Lp(a)
17. **Weekly Check-in** — Sunday review with score + bio age delta
18. **PDF Report** — branded, graph-rich, fully personal (UI/UX template attached separately)
19. **Red-Flag Detector** — runs on every message
20. **Educational Micro-Lessons** — 60-second explainers on demand

---

## 2. Tech Stack

```
Language:        Python 3.11+ (backend) | TypeScript + React (PPG/FaceAge web mini-app)
LLM:             Google Gemini API (Gemini 2.x, vision-enabled for BP photos, lab reports, fitness screenshots, FaceAge)
WhatsApp:        Pluggable provider — pick ONE of:
                   - Meta WhatsApp Business Cloud API (recommended)
                   - Twilio WhatsApp API
                   - WATI / Gupshup / Interakt (faster to ship in India)
Backend:         FastAPI
PPG mini-app:    Vite + React + TypeScript, deployed at miniapp.psquare.health (or subpath)
                 Camera: getUserMedia({video: {facingMode: 'environment'}})
                 Signal processing: see §10.3 — peak detection + RMSSD on green channel
Async queue:     Celery + Redis (PDF jobs, image processing)
Database:        PostgreSQL
Object storage:  S3-compatible (BP photos, fitness screenshots, FaceAge selfies, generated reports, raw PPG signals)
PDF generation:  WeasyPrint (HTML→PDF) + Matplotlib/Plotly for charts and the dial
OCR / vision:    Gemini Vision (BP readings, step counts, lab values, FaceAge)
Auth/secrets:    python-dotenv local; AWS Secrets Manager / Doppler in prod
Mini-app auth:   Short-lived signed JWT in URL, single-use, 15-min expiry
Deployment:      Docker + docker-compose locally; Fly.io / Railway / AWS for prod
Logging:         structlog → JSON; Sentry for errors
Testing:         pytest, pytest-asyncio, vcrpy for replays; Playwright for mini-app E2E
```

### 2.1 Required environment variables (`.env.example`)
```
GEMINI_API_KEY=
WHATSAPP_PROVIDER=meta|twilio|wati|gupshup
WHATSAPP_API_KEY=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
S3_BUCKET=
S3_ACCESS_KEY=
S3_SECRET_KEY=
SENTRY_DSN=
APP_BASE_URL=
MINIAPP_BASE_URL=               # e.g. https://miniapp.psquare.health
MINIAPP_JWT_SECRET=             # signs the short-lived mini-app links
ADMIN_PHONE_NUMBERS=
```

---

## 3. Repository Structure

```
psquare/
├── CLAUDE.md
├── README.md
├── .env.example
├── docker-compose.yml
├── pyproject.toml
├── app/                              ← Python backend
│   ├── main.py                       ← FastAPI entry, /webhook for WhatsApp, /miniapp/* APIs
│   ├── config.py
│   ├── whatsapp/
│   │   ├── adapter_base.py
│   │   ├── adapter_meta.py
│   │   ├── adapter_twilio.py
│   │   └── router.py
│   ├── conversation/
│   │   ├── state_machine.py
│   │   ├── intent_router.py
│   │   └── prompts/
│   ├── heart/                        ← CORE
│   │   ├── score.py                  ← P² Heart Score formula
│   │   ├── qrisk3.py
│   │   ├── framingham.py
│   │   ├── heart_age.py
│   │   ├── scoreboard.py
│   │   ├── bp_log.py
│   │   ├── rhr_log.py
│   │   ├── steps_log.py
│   │   ├── habits.py
│   │   ├── meal_suggester.py
│   │   ├── workout_planner.py
│   │   ├── stress_practice.py
│   │   ├── smoker_protocol.py
│   │   └── lab_cadence.py
│   ├── ppg/                          ← NEW
│   │   ├── session.py                ← issues signed mini-app links, stores results
│   │   ├── signal_validator.py       ← validates client-computed metrics
│   │   ├── stress_index.py           ← composite stress/fatigue from HR + HRV
│   │   └── interpreter.py            ← LLM-explained results in plain English
│   ├── bioage/                       ← NEW
│   │   ├── questionnaire.py          ← the 5-question intake
│   │   ├── face_age.py               ← Gemini Vision call + structured parse
│   │   ├── compute.py                ← combines questionnaire + face → bio age
│   │   └── reversal_plan.py
│   ├── medical_knowledge/            ← HARD-CODED, CITED, NOT LLM-GENERATED
│   │   ├── reference_ranges.py
│   │   ├── risk_scores.py            ← QRISK3 + Framingham coefficients
│   │   ├── heart_age_table.py
│   │   ├── hrv_norms.py              ← age/sex-stratified RMSSD norms
│   │   ├── bioage_weights.py         ← phenotypic-age inspired weights
│   │   ├── red_flags.py
│   │   ├── indian_thresholds.py
│   │   └── sources.md                ← citations + accessed dates
│   ├── personalization/
│   │   ├── profile_builder.py
│   │   ├── plan_generator.py
│   │   └── grounding.py
│   ├── reports/
│   │   ├── pdf_builder.py
│   │   ├── dial.py                   ← Heart Score dial SVG/PNG
│   │   ├── bioage_visual.py          ← bio-age vs chrono-age visual
│   │   ├── ppg_chart.py              ← waveform + HRV scatter
│   │   ├── charts.py
│   │   └── templates/
│   │       └── report.html
│   ├── db/
│   │   ├── models.py
│   │   └── migrations/
│   └── utils/
│       ├── gemini_client.py
│       ├── safety.py
│       └── i18n.py                   ← English / Hindi / Marathi / Hinglish
├── miniapp/                          ← NEW: TypeScript/React web app for PPG + FaceAge capture
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── routes/
│   │   │   ├── PpgScan.tsx
│   │   │   └── FaceCapture.tsx
│   │   ├── ppg/
│   │   │   ├── camera.ts             ← getUserMedia, torch on, exposure lock
│   │   │   ├── signal.ts             ← extracts green channel, bandpass, peak detect
│   │   │   ├── hrv.ts                ← RMSSD, SDNN, pNN50
│   │   │   └── quality.ts            ← signal quality index, retake logic
│   │   └── api.ts                    ← posts results back to backend with JWT
│   └── public/
├── tests/
└── scripts/
    ├── seed_demo_user.py
    └── send_test_report.py
```

---

## 4. WhatsApp Conversation Design

### 4.1 First-time user flow
1. User sends *anything* → bot replies with welcome + consent:
   > *"Hi 👋 I'm P Square — I help you understand your heart health and biological age, personally. I'll ask 12 quick questions, then offer a 30-second finger-on-camera scan and a face selfie. You'll get your **Heart Score**, **Biological Age**, and a plan that's actually yours. Reply **YES** to start."*
2. On YES → onboarding (§5), max 12 questions.
3. After onboarding:
   - Compute Heart Score → send dial + scoreboard
   - Offer optional **PPG scan** (link to mini-app)
   - Offer optional **Biological Age** (5 Qs + selfie)
   - Generate full PDF and send
4. Schedule 7-day check-in.

### 4.2 Returning user flow
The `intent_router` classifies each incoming message into:
`log_bp` | `log_rhr` | `log_steps` | `log_habit` | `request_score` | `request_report` | `start_ppg` | `start_bioage` | `update_metric` | `ask_question` | `red_flag` | `smalltalk`

### 4.3 Message types to support
- **Text** (primary)
- **Voice notes** → Gemini transcription → process as text
- **Images:**
  - BP monitor → Gemini Vision extracts SBP/DBP/pulse
  - Fitness app screenshot → step count + active minutes
  - Lab report → lipid + HbA1c values
  - **Face selfie → FaceAge** (handled in §11)
- **Mini-app links** → for PPG scan and FaceAge capture (camera access requires browser)
- **Buttons & list messages** → use WhatsApp interactive messages wherever possible

### 4.4 Daily / Weekly nudges (opt-in)
- **Morning (8 AM local):** *"Good morning, Rohan ☀️ Quick PPG scan? Tap → [link]. Or count your pulse manually for 30s and reply with the number ×2."*
- **Evening (9 PM local):** habits check-in (6 buttons)
- **Sunday (10 AM local):** weekly review with score delta and bio-age delta
- **Monthly:** "Time for a fresh PPG scan + FaceAge selfie to track your reversal plan."

### 4.5 Tone
Warm, curious, never judgemental. Short messages, broken into 2–3 bubbles. First-name often. Mirrors the user's language. Tasteful emojis.

---

## 5. Onboarding — Heart-Specific Intake (Max 12 Questions)

Strict cap. Use **WhatsApp interactive lists/buttons**, not free text. If a question can be skipped (no value to user this turn), skip it.

**The 12 questions:**
1. **Name + age + sex** (one combined message with text input)
2. **City** (text)
3. **Height + weight + waist** (one message; waist is critical for South Asians — explain how to measure with one line)
4. **Most recent BP** (button: "Don't know" allowed)
5. **Most recent lipid panel** (LDL/HDL/Trig/Total — paste values or "Don't know")
6. **HbA1c or fasting glucose** ("Don't know" allowed)
7. **Diagnosed conditions** (multi-select list: hypertension / high cholesterol / diabetes / heart attack / stent / bypass / AFib / heart failure / stroke / none)
8. **Current cardiac/BP/lipid medications** (text or "none")
9. **Family history** (one button: parent/sibling with heart attack/stroke/sudden cardiac death — Yes under 55 / Yes under 65 / Yes older / No / Don't know)
10. **Smoking status** (button: never / former / current — if current, ask cigs/day in sub-step)
11. **Activity + diet snapshot** (one combined message: typical daily steps band + veg/non-veg/eggetarian + cuisine)
12. **Sleep + stress** (sleep hours band + stress 1–10)

> **Implementation note:** Each answer stored with timestamp + source (`self_reported` / `lab_uploaded` / `photo_extracted` / `derived`). Use `null` for "Don't know" values; the Heart Score's confidence flag handles missing data gracefully.

After Q12, the bot says:
> *"That's it — 12 questions done 🎉 Want me to compute your Heart Score now? While I do that, I can also offer two optional 1-minute add-ons: a **PPG scan** (finger on camera) and a **Biological Age** check. Tap whichever you want."*

Buttons: `Heart Score now` · `Add PPG scan` · `Add Biological Age` · `All three`

---

## 6. The Pre-PPG Mini-Questionnaire (Max 3 Questions)

Just before launching a PPG scan, the bot asks **at most 3 short context questions** — these dramatically improve interpretation accuracy without hurting completion.

1. **State right now:** "How are you feeling?" → buttons: Calm · Normal · Stressed · Just exercised · Just woke up · Tired
2. **Caffeine in the last 60 min?** → Yes / No
3. **Anything affecting your heart right now?** (only shown if user reports any symptom keywords): "I'm OK" · "Slight palpitations" · "Feeling anxious"

> If user just exercised or had caffeine, the bot tells them: *"Got it — wait 10 min and we'll get a cleaner reading. I'll remind you."* and reschedules.

These 3 answers become metadata stored alongside the PPG result, and inform the LLM-generated interpretation.

---

## 7. The P² Heart Score — Exact Formula

This is deterministic Python in `app/heart/score.py`. The LLM does NOT compute it.

```
P² Heart Score (0–100) = 100 − weighted_penalty

weighted_penalty = (
    0.35 * cv_risk_penalty       # from QRISK3 / Framingham, 10-yr risk %
  + 0.15 * heart_age_penalty     # heart age − chronological age
  + 0.25 * lifestyle_penalty     # composite of BP, lipids, smoking, activity, diet, sleep, stress, alcohol, BMI/waist
  + 0.15 * condition_penalty     # known CVD, diabetes, family history modifiers
  + 0.10 * ppg_penalty           # NEW: HR, HRV, stress index from PPG scan (within last 7 days)
)
```

**If no recent PPG (<7 days), the 10% PPG weight is redistributed proportionally to the other four categories**, and the score's confidence flag drops one level.

**Each sub-penalty is normalized 0–100 with documented thresholds in `medical_knowledge/`.**
- `cv_risk_penalty`: 10-yr CV risk 0% → 0; 30%+ → 100; linear.
- `heart_age_penalty`: heart age = chronological → 0; +20 yrs older → 100.
- `lifestyle_penalty`: average of pillar penalties.
- `condition_penalty`: prior MI/stroke/stent → 100; T2D unmedicated → 70; well-controlled HTN on meds → 30; FH early CVD → 40; clean → 0.
- `ppg_penalty`: see §10.5.

**Confidence flag:** >30% inputs missing → `Low`; 10–30% → `Medium`; else `High`. Displayed on the dial.

**Never let the LLM modify the score.** The LLM only *explains* the score; the number is computed.

### 7.1 QRISK3 inputs
Age, sex, ethnicity (allow "South Asian Indian" — large effect), smoking, diabetes, family history of CHD < 60, CKD stage, AF, BP treatment, RA, SBP, BP variability, Total/HDL ratio, BMI, deprivation (default for India). Use the official QRISK3 algorithm.

### 7.2 Framingham fallback
When QRISK3 inputs aren't available. Inputs: age, sex, total chol, HDL, SBP, BP treatment, smoking, diabetes.

### 7.3 Heart Age
JBS3 / QRISK3 method: the age at which someone with all-optimal risk factors would have the same 10-yr CV risk as the user.

---

## 8. The Heart Scoreboard

Rendered both as a WhatsApp message (compact) and a full-page PDF section.

For **each pillar** the renderer outputs:
1. Current value
2. Status band (color)
3. One-line plain-English explanation, with the user's data baked in
4. The single highest-impact action to move it up
5. How many points it's currently costing the Heart Score

**Example pillar output (filled by LLM from structured inputs):**
> **Blood Pressure — 138/86 — Stage 1 (Amber).** *Costing your Heart Score 6 points.*
> "Your 7-day average is above 130/80. The biggest lever for you is sodium — based on your diet pattern, your daily intake is likely 8–10g (target: under 5g)."
> **Highest-impact action:** Cut packaged snacks and table salt for 14 days; re-check BP daily. Expected drop: 4–8 mmHg systolic.

---

## 9. Personalization — How Plans Become Personal

### 9.1 Anti-generic guardrail
Before sending any plan, `plan_generator` runs a **specificity check**:
- Plan mentions user's name, age, weight, and at least 2 specific data points (BP / lipid / RHR / waist / family hx / step count / HRV / bio age)
- Each cardio prescription cites available time + equipment + joint limitations
- Each meal suggestion cites cuisine + diet preference + sodium target
- If any check fails → regenerate with stronger grounding, do NOT send.

### 9.2 LLM grounding template
```
SYSTEM: You are a P Square specialist for [module]. You ONLY use the user's
data below. You do NOT invent facts. You cite the data point behind every
recommendation in parentheses, like "(per your LDL of 142)".

USER PROFILE:
{full_profile_json}

USER'S CURRENT P² HEART SCORE BREAKDOWN:
{score_breakdown_json}

LATEST PPG (if available):
{ppg_json}

LATEST BIO AGE (if available):
{bioage_json}

MEDICAL RULES YOU MUST FOLLOW:
{relevant_rules_from_medical_knowledge}

RED FLAGS — if any are present, output {"escalate": true, "reason": "..."} and stop:
{red_flag_list}

TASK:
{task_specific_prompt}

OUTPUT FORMAT:
{strict_json_schema}
```

The LLM **never** outputs prose directly to the user. It outputs structured JSON which a deterministic renderer converts into WhatsApp messages or PDF sections.

### 9.3 Refresh cadence
- **Heart Score:** recomputed on every metric update (BP, RHR, steps, lab, smoking, PPG, bio age)
- **Cardio + strength plan:** every 14 days, or on score change > 5
- **Meal suggestions:** on demand
- **Lab cadence:** every 90 days, or on lab upload
- **Biological age:** monthly re-check encouraged

---

## 10. PPG Vitals Scan (NEW)

### 10.1 Why a web mini-app
WhatsApp does not allow live camera streams inside the chat. The cleanest user experience is:
1. Bot sends a short message + tappable link
2. Link opens a mobile browser page (PWA-style, tiny payload, no install)
3. Page asks for camera permission, runs the 30-second scan, computes results client-side
4. Page POSTs results back to the backend with a signed JWT
5. Bot receives the result and replies with interpretation in WhatsApp

### 10.2 Mini-app UX flow
1. Page loads → big "Start scan" button + 6-second animated explainer (where to place finger, torch will turn on)
2. User places **index or middle finger** firmly over the **back camera + flash**
3. Torch turns on, exposure locked
4. 5-second pre-roll for stabilization (countdown shown)
5. **30-second recording** — live waveform shown, signal-quality bar
6. If signal quality < threshold → ask user to re-position, retake
7. Compute HR, HRV (RMSSD, SDNN, pNN50), Stress Index (§10.4)
8. Show summary card → tap "Send to my P Square" → POST to backend
9. Page closes → user returns to WhatsApp where the bot has already posted the interpretation

### 10.3 Signal processing (client-side, TypeScript)
- Capture frames at ≥ 30 fps via `requestAnimationFrame` + `canvas.drawImage`
- Extract **green channel** mean intensity per frame (green has best PPG signal)
- Detrend: subtract moving average (window ~1 sec)
- Bandpass filter: 0.7–4.0 Hz (covers 42–240 BPM)
- **Peak detection:** find local maxima with min-distance based on physiological HR
- **Inter-Beat Intervals (IBI):** array of ms between peaks
- **Quality checks:** discard if <20 valid peaks, or IBI std-dev too high, or signal-to-noise too low → ask user to retake
- **HR (BPM):** 60000 / mean(IBI)
- **HRV metrics:**
  - **RMSSD** — root mean square of successive IBI differences (primary HRV metric)
  - **SDNN** — std-dev of all IBIs
  - **pNN50** — % of consecutive IBI pairs differing by >50 ms

### 10.4 Stress / Fatigue Index (server-side, deterministic)
Composite 0–100 (higher = more stress/fatigue), computed from:
- HR vs personal resting baseline (elevation = ↑stress)
- RMSSD vs age/sex-adjusted norm in `medical_knowledge/hrv_norms.py` (lower RMSSD = ↑stress)
- HR/HRV ratio (LF/HF approximation when long enough recording allows)
- Pre-scan questionnaire metadata (caffeine, just-exercised, anxiety) — used to *adjust* the index, not as input to the user-facing score

Bands: Low (0–30) · Moderate (31–60) · High (61–100).

### 10.5 PPG penalty contribution to Heart Score (§7)
```
ppg_penalty = average of:
  - hr_penalty       (0 if RHR within personal optimal band; rises linearly above)
  - hrv_penalty      (0 if RMSSD ≥ age-adjusted median; rises as RMSSD drops)
  - stress_penalty   (= stress_index)
```

### 10.6 Safety & honest framing
- The mini-app **must display this disclaimer before scan starts**:
  > *"This scan estimates your heart rate, heart-rate variability, and stress level from your finger over the camera. It is for wellness insight only — it is NOT a medical-grade ECG or pulse oximeter, and cannot diagnose arrhythmias or any condition. If you feel unwell, contact a doctor."*
- If HR < 40 or > 130, or detected irregular IBI pattern → bot suggests "this looks irregular — please consult a cardiologist; consider an ECG".
- Raw signal optionally retained (S3, encrypted, 30-day retention default, user can opt out).

### 10.7 LLM interpretation
After backend receives the metrics, an LLM call generates 2–3 short WhatsApp bubbles:
- One sentence summary ("Your HR was 72 bpm, HRV 38 ms, stress index 42 — moderate.")
- One sentence personalized insight (cites data) ("Your HRV is below the median for your age — likely tied to your 5.5 hours of sleep last night and high stress score.")
- One specific action ("Try the 4-7-8 breathing practice tonight before bed; we'll re-scan tomorrow morning.")

---

## 11. Biological Age Module (NEW)

### 11.1 What it returns
- A single number: **estimated biological age**
- Gap vs chronological: "younger by N years" / "on par" / "older by N years"
- **Top 3 drivers** (from face + questionnaire), each with one specific action
- **60-day reversal plan** — sleep, sun, hydration, sugar, alcohol, skincare basics, cardio, stress

### 11.2 The 5-question questionnaire (max 5 — strict)
Use WhatsApp interactive buttons.
1. **Sleep:** "Average hours of actual sleep per night?" → buttons: <5 / 5–6 / 6–7 / 7–8 / 8+
2. **Sun:** "Daily outdoor sun exposure (without sunscreen on body)?" → None / <15 min / 15–60 min / 1+ hr
3. **Sugar + processed food:** "How often do you eat sweets, packaged snacks, sugary drinks?" → Daily / 3–5×/wk / 1–2×/wk / Rarely
4. **Smoking + alcohol:** "Smoke or drink regularly?" → Both / Smoke only / Drink only / Neither
5. **Stress + activity:** "Most days I feel..." → Energized & active / OK / Tired / Exhausted

These map to a numeric phenotypic-age-style adjustment in `bioage/compute.py`.

### 11.3 Face capture — also via mini-app
Why: WhatsApp compresses images aggressively, hurting Gemini Vision accuracy. The mini-app captures a higher-quality, properly-framed selfie:
- Asks the user to face a window in soft daylight
- Provides an oval guide overlay + auto-capture when alignment is good
- Captures one front-facing image at 1024×1024 minimum
- POSTs encrypted to backend

### 11.4 Face → Gemini Vision call
Prompt strictly instructs Gemini to evaluate **observable visible markers only**:
- Skin texture and tone uniformity
- Periorbital fine lines, eye-area puffiness
- Nasolabial and forehead lines
- Pigmentation, redness, dullness
- Lip volume, jawline definition (where visible)

Returns structured JSON:
```json
{
  "estimated_face_age": 38,
  "confidence": "Medium",
  "visible_drivers": [
    {"factor": "Sun damage", "evidence": "Pigmentation across upper cheeks", "severity": "moderate"},
    {"factor": "Sleep deficit", "evidence": "Periorbital darkness and puffiness", "severity": "moderate"},
    {"factor": "Dehydration / dryness", "evidence": "Reduced skin reflectance", "severity": "mild"}
  ]
}
```

**Hard rule for the prompt:** Gemini must NOT comment on weight, ethnicity, attractiveness, gender expression, emotion, or anything not directly relevant to visible age markers. If the photo isn't usable (blurry, too dark, multiple faces, sunglasses, mask), it returns `{"usable": false, "reason": "..."}`.

### 11.5 Final biological age
```
biological_age = chronological_age
               + 0.6 * (face_age − chronological_age)
               + lifestyle_adjustment_from_questionnaire
               + objective_data_adjustment      # uses BP, lipid, BMI, waist, smoking, HbA1c, HRV if available
```

The `bioage_weights.py` file contains the exact coefficients (inspired by phenotypic-age methods like Levine PhenoAge — but clearly framed as an *estimate*, not a clinical biomarker).

### 11.6 Reversal plan
Specific, measurable, 60-day plan with weekly milestones, citing the user's drivers. Re-scan offered every 30 days.

### 11.7 Honest framing (mandatory)
Every bio-age output ends with:
> *"This is an estimate from your face and lifestyle answers — it's a useful directional signal for tracking lifestyle changes, but it is not a medical biomarker."*

---

## 12. Sub-feature Specs (Heart Health Support)

### 12.1 BP Logging
- Accepts: `"BP 132/84 78"`, `"132 over 84"`, voice note, or photo of BP monitor.
- Photo path: Gemini Vision extracts SBP/DBP/pulse. Confirm before saving.
- 7-day rolling average; chart in PDF.
- Alerts: SBP ≥ 180 or DBP ≥ 120 → red-flag escalation. SBP 160–179 or DBP 100–119 → "please consult your doctor this week".

### 12.2 Resting Heart Rate Logging
- Manual: "count your pulse for 30s ×2"
- PPG: auto-feeds RHR if scan done within last 24h on waking
- Apple Watch / Mi Band / Fitbit screenshots accepted via Vision
- 7-day average shown on scoreboard
- Flags: RHR > 100 sustained → escalate

### 12.3 Steps Tracking
- Manual or screenshot from Google Fit / Mi Fit / Apple Health / Samsung Health
- Personalized step goal: current avg + 1500, +500 every 2 weeks, capped at 12k unless user opts higher
- Trend chart in PDF

### 12.4 Daily Heart Habits Checklist
Six tappable buttons each evening:
1. 🚶 Hit my step goal
2. 🥗 ≥ 2 servings veg/fruit
3. 🧂 Kept salt low
4. 🚭 No smoke / vape today (only for current/former smokers)
5. 😴 In bed before 11 PM
6. 🧘 Did the 5-min breathing practice

Streaks tracked; small contribution to lifestyle pillar of Heart Score.

### 12.5 Personalized Cardio + Strength Plan
**Cardio (Zone 2 + intervals):**
- Zone 2 target HR via Karvonen using user age and RHR
- Equipment- and joint-aware
- Starts where the user *is*, +10% volume per week for 4 weeks, then deload

**Strength (heart-relevant):**
- 2× per week, full-body, compound moves only
- Bodyweight default; scales with available equipment

### 12.6 Heart-Healthy Meal Suggestions
On-demand. Bot returns 2–3 meal options grounded in cuisine, veg/non-veg, allergies, sodium target (BP-driven), LDL target (lipid-driven), caloric range (waist-driven), and time of day.

### 12.7 Stress & HRV Micro-Practice
Daily 5-min practice picked once during onboarding from {box breathing, 4-7-8 breathing, walk + slow breathing, gratitude journal, prayer/meditation}. Streak tracked. **PPG-adaptive:** if HRV trends down for 3 consecutive scans, bot suggests a different practice.

### 12.8 Smoker's Reduction Protocol
Opt-in only. Progressive reduction with replacement behaviors. Connects to Indian National Tobacco Cessation helpline (1800-11-2356).

### 12.9 Lab Cadence Recommender
- **Lipid profile** — every 12 mo if normal; every 3–6 mo if abnormal or on statin
- **HbA1c / FPG** — annual if normal
- **BP** — daily–weekly home if elevated; clinic 6–12 mo otherwise
- **ECG** — baseline at 35+; sooner if symptoms or PPG flags irregular IBIs
- **hsCRP, Lp(a), ApoB** — once-in-lifetime baseline for Lp(a) (huge for South Asians); hsCRP per physician

### 12.10 Weekly Check-in (Sunday)
- Heart Score this week vs last (delta + chart)
- Bio-age delta if recent re-check
- PPG trend (HR + HRV + stress) over the week
- Pillar that improved most + pillar needing attention
- One specific action for the next 7 days

### 12.11 Educational Micro-Lessons
60-second explainers, on demand. Examples: LDL, heart age, QRISK3, HRV, what RMSSD means, why face age tracks lifestyle, why Lp(a) matters.

---

## 13. PDF Report — The Showpiece

### 13.1 Branding
P² monogram. Suggested palette: deep teal `#0F766E`, soft cream `#FAF7F2`, charcoal `#1F2937`, accent coral `#F97366`, success green `#10B981`, warning amber `#F59E0B`, danger red `#EF4444`. Sans-serif (Inter or DM Sans).

> ⚠️ The user will attach the desired report design separately. Match it pixel-faithfully when provided. Until then, use the structure below as scaffold.

### 13.2 Sections (v1.1 order)
1. **Cover** — Name, report date, P² logo, "Your Heart & Longevity Report"
2. **Hero — P² Heart Score + Biological Age side by side** (the two big numbers)
3. **Heart Scoreboard** — 10 pillars (incl. PPG-derived HRV and stress)
4. **PPG Snapshot** — last scan: HR, HRV, stress, waveform thumbnail, trend over time
5. **10-Year Cardiovascular Risk** — QRISK3/Framingham %, peers comparison, top drivers
6. **Heart Age** — heart age vs chronological, big number, chart
7. **Biological Age** — bio age vs chronological, top 3 visible/lifestyle drivers, 60-day reversal plan
8. **Trends** — score over time, BP, RHR, steps, HRV, lipid (if multiple readings)
9. **Your Personalized Cardio + Strength Plan** — week view + progression chart
10. **Heart-Healthy Eating Principles for You**
11. **Daily Habits & Stress Practice**
12. **Your Lab Cadence**
13. **What I'll Watch Going Forward**
14. **Glossary & Citations**
15. **Disclaimer & Doctor-Visit Encouragement** — full-page

### 13.3 Charts
- **Heart Score Dial** — half-circle SVG gauge, color-banded
- **Bio Age vs Chrono Age** — twin-bar visual with age delta callout
- **PPG waveform thumbnail** + HRV scatter
- **Score over time** — last 12 weeks
- **BP trend** — dual-line with reference bands
- **RHR + HRV trend** — dual-axis line
- **Steps trend** — bar chart with goal line
- **Lipid panel** — grouped bar with reference markers
- **Risk drivers** — horizontal bar showing points each pillar costs

All charts: brand palette, 1-line plain-English caption, user's data labeled vs reference.

### 13.4 Pipeline
1. Pull profile + plans + score history + PPG history + bio-age history from DB
2. Render `templates/report.html` with Jinja2
3. Inline CSS, embed charts as base64 SVG/PNG
4. WeasyPrint → PDF
5. Upload to S3 → signed URL
6. Send PDF via WhatsApp document message

---

## 14. Database Schema (v1.1 essentials)

```python
User(id, phone, name, dob, sex, ethnicity, language, city, tz, created_at, consent_given_at)
Profile(user_id, height_cm, weight_kg, waist_cm, version, updated_at)
MedicalHistory(user_id, condition, since, status, notes)
Medication(user_id, name, dose, frequency, since)
FamilyHistory(user_id, relation, condition, age_of_onset)
LabResult(user_id, test_name, value, unit, ref_low, ref_high, taken_on, source)
BPReading(user_id, systolic, diastolic, pulse, taken_at, posture, source)
RHRReading(user_id, bpm, taken_at, source)
StepsLog(user_id, date, steps, active_minutes, source)
HabitLog(user_id, date, habits_json, streak_count)
SmokingLog(user_id, date, cigarettes)
HeartScore(user_id, score, breakdown_json, confidence, computed_at)
PPGScan(user_id, taken_at, hr_bpm, rmssd_ms, sdnn_ms, pnn50_pct, stress_index,
        signal_quality, raw_signal_url, pre_scan_context_json, source_device)
BioAgeAssessment(user_id, taken_at, biological_age, chronological_age,
                 face_image_url, face_age_estimate, face_drivers_json,
                 questionnaire_json, computed_breakdown_json)
Plan(user_id, type, version, payload_json, created_at, active)  # cardio | strength | meals | lifestyle | lab_cadence | bioage_reversal
Conversation(id, user_id, started_at, last_msg_at)
Message(conversation_id, direction, content, media_url, intent, ts)
Report(user_id, version, pdf_url, generated_at)
Checkin(user_id, scheduled_for, type, completed_at)
MiniAppSession(id, user_id, type, jwt_jti, issued_at, expires_at, used_at, result_id)
```

Use Alembic for migrations. Soft-delete only.

---

## 15. Safety, Privacy & Compliance

### 15.1 Mandatory safety behaviors
**Red-flag detector** runs on every inbound message + on every PPG result. Heart-specific triggers:
- Chest pain / pressure / tightness
- Sudden severe shortness of breath at rest
- FAST stroke symptoms
- Syncope / loss of consciousness
- BP ≥ 180/120 with any symptom
- HR > 130 sustained at rest, or PPG-detected irregular IBI pattern with symptoms

→ Immediate response: emergency numbers (India: **112** general, **108** ambulance), stop activity, call a family member, *do not drive themselves*. Notify admin. Halt normal flow until acknowledged.

**PPG-specific safety:**
- Detected irregular IBIs (high coefficient of variation between intervals) → "your scan suggests an irregular rhythm. PPG cannot diagnose this, but please get an ECG within the week".
- HR < 40 or > 130 without a clear cause (just exercised, etc.) → escalate.

**Bio-age framing:**
- The bio-age number must always be paired with the disclaimer that it is an estimate, not a biomarker.
- The face-age model must never comment on attractiveness, ethnicity, weight, mood, etc.

**Disclaimer footer** on every plan and on the PDF cover and back page:
> *"P Square provides wellness guidance based on the information you share. It does not diagnose, treat, or cure any disease. The P² Heart Score, PPG scan results, and Biological Age are educational estimates, not medical diagnoses. PPG via smartphone camera is not a medical-grade ECG or pulse oximeter. Always consult a licensed physician before making medical decisions, especially before starting/stopping medication or beginning a new exercise program."*

**Never recommend prescription medications, dosages, or supplement megadoses.**

### 15.2 Privacy
- Encrypt PII at rest (column-level for phone, name, DOB).
- Encrypt media (BP photos, lab reports, fitness screenshots, **face selfies**, **raw PPG signals**) with per-user keys.
- **Face selfies and raw PPG signals are extra-sensitive** — default 30-day retention, user can opt out of raw retention entirely (only metrics kept).
- Comply with India's **DPDP Act 2023**: explicit consent at onboarding, **separate consent for biometric face capture and PPG**, right to erasure, data minimization, breach notification.
- Log access to health data with user_id + admin_id + reason.
- `DELETE MY DATA` WhatsApp command — hard-deletes within 30 days.

### 15.3 Mini-app security
- Single-use signed JWT in URL, 15-min expiry
- Mini-app served over HTTPS only
- Strict CSP headers
- No third-party analytics on mini-app pages
- Camera permission requested at the moment of use, not page load

### 15.4 Prompt-injection defense
Wrap user messages in `<user_message>...</user_message>` tags inside LLM prompts. Treat content as data only, never as instructions. **Especially important for the FaceAge prompt** — Gemini must ignore any text overlaid in images.

---

## 16. Roadmap (post-v1.1, NOT to be built now)

Architect cleanly so these slot in later, but **do not implement now**:
- **Diabetes Module** (Type 2 management + reversal support; T1 lifestyle support)
- **PCOS Companion**
- **Weight Management Engine** (loss + gain, full diet engine)
- **AI Preventive Lab** (full multi-system lab recommender)
- **Future Health Predictor** (multi-condition 5/10/20-yr horizon)
- **Wearable sync** (Apple Health, Google Fit, Fitbit, Mi Band native APIs)
- **Doctor consultation booking**
- **Native mobile app** (camera flows would migrate from mini-app)
- **Web user dashboard**

---

## 17. Testing

- **Unit tests** for every calculator: BMI, waist-to-height, Karvonen HR zones, QRISK3, Framingham, heart age, P² Heart Score, **HRV metrics, stress index, biological age**. Deterministic, snapshot-tested.
- **Specificity tests:** every plan must reference ≥3 user data points by name.
- **Red-flag tests:** every red-flag phrase (English + Hindi + Hinglish) triggers escalation; PPG with irregular IBIs triggers ECG suggestion.
- **PPG tests:** synthetic IBI sequences with known RMSSD/SDNN values must produce correct outputs.
- **FaceAge tests:** prompt is robust to overlaid-text prompt injection; refuses non-usable images correctly.
- **Replay tests** with vcrpy for WhatsApp + Gemini.
- **Mini-app E2E:** Playwright scripts for camera-permission flow + JWT validation.
- **Demo user:** `scripts/seed_demo_user.py` creates a 42-yr-old Indian male, smoker (10/day), BP 138/86, LDL 142, HDL 38, sedentary desk job, father had MI at 54 — full E2E target including PPG and bio age.

---

## 18. Build Order (v1.1, phased)

**Phase 1 — Skeleton (Week 1)**
- Repo, Docker, FastAPI, DB models, `.env.example`
- WhatsApp adapter (one provider), `/webhook` echoing
- Gemini client with structured (JSON) output

**Phase 2 — Onboarding + Heart Score (Week 2–3)**
- 12-question onboarding state machine via WhatsApp interactive messages
- Profile persistence + edit flow
- Red-flag detector
- `medical_knowledge/` populated with cited rules
- QRISK3, Framingham, heart age, lifestyle pillar scores
- P² Heart Score composer
- Scoreboard assembler

**Phase 3 — Logging + plans (Week 3–4)**
- BP / RHR / steps logging (text + voice + photo via Gemini Vision)
- Daily habits checklist
- Smoker protocol (opt-in)
- Cardio + strength plan generator
- Meal suggester (on-demand)
- Stress micro-practice
- Lab cadence recommender
- Specificity guardrail

**Phase 4 — PPG mini-app (Week 4–5)**
- Vite/React mini-app skeleton
- Camera capture, torch, signal processing pipeline
- HR / HRV / stress index computation
- Pre-scan 3-question questionnaire in WhatsApp
- Backend `app/ppg/` integration + interpretation prompts
- Safety checks (irregular IBI detection)

**Phase 5 — Biological Age (Week 5–6)**
- 5-question intake via WhatsApp interactive buttons
- Mini-app FaceCapture page (oval guide, soft daylight prompt)
- `bioage/face_age.py` — Gemini Vision call with strict prompt
- `bioage/compute.py` — final biological age formula
- Reversal-plan generator

**Phase 6 — PDF Report (Week 6–7)**
- Wait for UI/UX file from user; implement template + dial + bio-age visual + PPG chart + WeasyPrint pipeline

**Phase 7 — Check-ins, polish, deploy (Week 7–8)**
- Daily morning/evening prompts, Sunday weekly review
- Educational lessons library
- DPDP compliance, admin dashboard
- Deploy backend + mini-app

---

## 19. Definition of Done (v1.1)
v1.1 is "done" when:
- [ ] A new user can complete onboarding via WhatsApp in under 5 minutes (≤ 12 questions)
- [ ] The bot returns the P² Heart Score dial as an image, with confidence tag
- [ ] The Heart Scoreboard shows all 10 pillars with status, explanation, and one action each
- [ ] BP, RHR, and steps can be logged via text, voice, or photo
- [ ] The user can complete a 30-second PPG scan via the mini-app and receive HR, HRV, and stress index plus a personalized interpretation in WhatsApp
- [ ] The PPG flow asks at most 3 pre-scan questions
- [ ] The user can complete the Biological Age module via 5 questions + a face selfie and receive bio age + 3 drivers + 60-day reversal plan
- [ ] A personalized cardio + strength plan is generated, citing ≥3 user data points
- [ ] On-demand meal suggestions return cuisine-, BP-, lipid-aware options
- [ ] PDF report generates in < 30 seconds, includes Heart Score dial + Bio Age + PPG sections, and matches the supplied UI/UX design
- [ ] Red-flag detection triggers on a curated test set (English + Hindi + Hinglish) including PPG irregular-IBI cases
- [ ] Daily and weekly check-ins are scheduled and delivered
- [ ] DPDP-compliant consent + delete flow works, with separate consent for biometric (face + PPG) capture
- [ ] Demo user end-to-end test passes
- [ ] ≥80% test coverage on `app/heart/`, `app/ppg/`, `app/bioage/`, and `app/medical_knowledge/`

---

## 20. Final Reminder

This product is for *real humans* with *real fear* about heart disease and aging — heart disease is the #1 killer of Indians, often striking 10 years earlier than in Western populations. Build with care.

The chatbot should never feel like a chatbot. It should feel like the friend you wish you had: who knows cardiology and longevity science, takes you seriously, remembers what you told them last week, and gives you a plan you actually believe is yours.

**If a recommendation can't be made personal, don't ship it.**

— End of CLAUDE.md (v1.1: Heart Health + PPG + Biological Age) —
