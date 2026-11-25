# DataHealer AI 🩺

**Autonomous Data Cleaning & AI Insights Agent**

> Drop any dirty CSV or Excel file → get a production-ready cleaned dataset, downloadable Python pipeline script, and AI-powered executive action brief — instantly.

---

## What it does

| Problem in your data | DataHealer fix |
|---|---|
| Missing / null values | Filled with median (numbers) or mode (text) |
| Duplicate rows | Detected and removed automatically |
| Broken or inconsistent dates | Parsed and normalized across common formats |
| Mixed-type columns (numbers stored as text) | Converted to correct numeric dtype |
| Messy column names | Lowercased and underscore-standardized |
| Trailing whitespace in text | Stripped across all string fields |

After cleaning:
- **Download cleaned CSV** — production-ready instantly
- **Download Python script** — the exact Pandas pipeline that did the work, ready to drop into any project
- **AI Insights Panel** — Gemini API audits the dataset and returns a data quality score, 3 key insights, 3 executive action items, and risk flags

---

## Tech Stack

```
Python 3.11+
Pandas 2.x          — data processing engine
Pydantic v2         — strict schema validation on cleaning output
Streamlit           — web UI
Google Gemini API   — AI-powered dataset insights (optional)
OpenPyXL            — Excel file support
```

---

## Run Locally

```bash
# 1. Clone or download this folder
cd datahealer-ai

# 2. Install dependencies
pip install streamlit pandas pydantic google-generativeai openpyxl

# 3. (Optional) Add your Gemini API key for AI insights
set GEMINI_API_KEY=your_key_here        # Windows
export GEMINI_API_KEY=your_key_here     # Mac/Linux

# 4. Launch
streamlit run app.py
```

The app opens at `http://localhost:8501`

A sample dirty dataset is included: `sample_dirty_data.csv`

---

## Project Structure

```
datahealer-ai/
├── app.py                  # Streamlit UI
├── cleaner.py              # Core cleaning engine + Pydantic validation
├── ai_insights.py          # Gemini API integration
├── sample_dirty_data.csv   # Test file with real-world data issues
└── README.md
```

---

## Why I built this

Real-world enterprise data is never clean. Before any analysis or model can produce reliable output, the upstream data layer needs robust, validated, automated processing.

This project is my working demonstration of how Python, schema validation, and LLM agents can be combined into a tool that immediately saves analysts hours of manual cleaning work.
