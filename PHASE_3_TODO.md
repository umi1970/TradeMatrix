# Phase 3: AI Agents - TODO Liste

**Status:** Phase 2 Complete (100%) ✅
**Nächste Phase:** Phase 3 AI Agents

---

## 🎯 Phase 3 Aufgaben

### 1. ChartWatcher Agent implementieren
**Status:** Pending
**Datei:** `services/agents/src/chart_watcher.py`
- OCR für Chart-Analyse (Tesseract oder Google Vision)
- Pattern Detection (EMAs, Support/Resistance, Candlesticks)
- LangChain Integration für AI-Analyse
- Integration mit Technical Indicators Module

### 2. SignalBot Agent implementieren
**Status:** Pending
**Datei:** `services/agents/src/signal_bot.py`
- MR-01: EMA-Cross Reversal
- MR-02: Pivot Rebound
- MR-03: Gap-Open Play
- MR-04: Vortagstief-Reversal (Priority Override)
- MR-05: End-of-Month Rotation
- MR-06: Yesterday Range Reversion (Priority Override)
- AI Signal Synthesis mit LangChain/GPT-4
- Integration mit ValidationEngine & RiskCalculator

### 3. RiskManager Agent finalisieren
**Status:** Pending
**Datei:** `services/agents/src/risk_manager_agent.py`
- Integration mit existing RiskCalculator
- Break-Even automation
- Position Size enforcement
- Multi-trade risk monitoring

### 4. JournalBot Agent implementieren
**Status:** Pending
**Datei:** `services/agents/src/journal_bot.py`
- Daily Briefing Generator (DOCX + JSON)
- Weekly Summary Generator
- AI Trade Analysis (Performance, Patterns, Insights)
- Matrix Branding (Farbcodes)
- Speicherung in `reports` Table + Supabase Storage

### 5. Publisher Agent implementieren
**Status:** Pending
**Datei:** `services/agents/src/publisher.py`
- Report Upload zu Blog/Subdomain
- Social Media Sharing (optional)
- SEO Optimization
- Automated Publishing Workflow

### 6. LangChain Integration Setup
**Status:** Pending
**Tasks:**
- OpenAI API Key Setup
- LangChain prompt templates
- Output parsers (Pydantic)
- Error handling & retry logic
- Rate limiting

### 7. AI Agent Tests schreiben
**Status:** Pending
**Dateien:**
- `tests/test_chart_watcher.py`
- `tests/test_signal_bot.py`
- `tests/test_journal_bot.py`
- `tests/test_publisher.py`

---

## ✅ Phase 2 Complete (Referenz)

- Technical Indicators ✅
- Morning Planner ✅
- US Open Planner ✅
- Alert Engine ✅
- Risk Calculator ✅
- Validation Engine ✅
- Unit Tests (275+) ✅
- E2E Tests (8) ✅

---

## 📊 Dependencies für Phase 3

```bash
# AI & LangChain
pip install langchain langchain-openai openai

# OCR (wähle eine)
pip install pytesseract pillow  # Option A: Tesseract (free)
pip install google-cloud-vision  # Option B: Google Vision (paid)

# Report Generation
pip install python-docx reportlab
```

---

## 🎯 Erfolgsmetriken Phase 3

- [ ] ChartWatcher erkennt Patterns (>80% Accuracy)
- [ ] SignalBot generiert valide Signale (alle 6 MR-Rules)
- [ ] JournalBot erstellt Daily Reports
- [ ] Publisher uploaded Reports
- [ ] AI Tests >70% Coverage

---

**Next Session Start Command:**
"Weiter mit Phase 3 AI Agents - sparsam mit Kontext!"
