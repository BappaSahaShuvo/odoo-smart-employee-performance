# Smart Employee Performance & Promotion Management System (Odoo 19)

## Overview
Enterprise Human Resource Performance & Promotion Management custom module built for Odoo 19 and Python 3.12. Automates KPI scoring, goal tracking, promotion evaluations, disciplinary actions, skill matrix management, and AI career guidance.

## Architecture
- **Backend:** Python 3.12, Odoo 19 ORM, PostgreSQL
- **Frontend:** Odoo OWL 2 Components, SCSS, QWeb
- **Reporting:** QWeb PDF Engine, XLSX, CSV Export
- **AI Integration:** OpenAI API and Local LLM (Ollama/vLLM) endpoint abstraction

## Key Workflows
1. **Goal Lifecycle:** Draft -> Submitted -> TL Approved -> Manager Approved -> Active -> Completed.
2. **KPI Engine:** $0.30(TC) + 0.20(A) + 0.20(T) + 0.15(F) + 0.15(I) - \text{Deductions}$.
3. **Promotion Policy:** Minimum 6 months service, Attendance $\ge 80\%$, Active Warnings $< 3$, Mandatory Training Completed, and KPI Score $\ge 75$.

## Local AI with Ollama (WSL Ubuntu)
1. Install Ollama inside the same WSL Ubuntu environment where Odoo runs.
2. Start Ollama and download a model such as `llama3.2`.
3. In Odoo Settings -> Smart Performance & AI, select `Local LLM (Ollama / vLLM)`, enable AI, set endpoint to `http://127.0.0.1:11434/api/chat`, and model to the installed model name.
4. The dashboard chat sends the user's prompt to `/smart_performance/ai_chat` and uses the live employee record as context.

## Report export
The Reports tab now provides working authenticated HTTP endpoints:
- `/smart_performance/export_kpi_xlsx`
- `/smart_performance/export_kpi_csv`
The buttons pass the active employee ID when available and download the live KPI records.
