# Smart Employee Performance & Promotion Management System

An enterprise-grade **Employee Performance, KPI, Promotion, Training, Goal, Attendance, and AI Management System** built as a custom module for **Odoo 19**.

The system provides role-based HR dashboards, automated KPI calculations, employee goal tracking, promotion eligibility evaluation, disciplinary warning management, training management, career paths, skill matrices, rewards, performance reviews, AI-powered performance analysis, and PDF/XLSX/CSV reporting.

---

## 📌 Project Overview

The **Smart Employee Performance & Promotion Management System** is designed to centralize employee performance management inside Odoo.

Instead of managing employee performance through spreadsheets and disconnected HR processes, this module provides an integrated workflow covering:

- Employee performance tracking
- KPI calculation
- Goal management
- Attendance monitoring
- Leave management
- Performance reviews
- Promotion requests
- Promotion history
- Training courses and enrollment
- Skill matrix management
- Career path management
- Employee rewards
- Disciplinary warnings
- Role-based dashboards
- AI-powered performance analysis
- HR analytics
- PDF/XLSX/CSV reports

The system uses Odoo's ORM, PostgreSQL, OWL, QWeb, scheduled actions, security groups, record rules, and external/local AI integrations.

---

# 🚀 Main Features

## 1. Employee Performance Management

The module extends the standard Odoo Employee functionality with performance-related information.

Performance information can include:

- Overall KPI score
- Attendance score
- Performance status
- Employee role
- Department
- Reporting hierarchy
- Service duration
- Active warnings
- Goals
- Training
- Promotion status
- Career development information

---

# 📊 2. KPI Management

The system provides a dedicated KPI management engine for measuring employee performance.

KPI-related functionality includes:

- KPI score calculation
- Attendance score
- Task completion
- Training performance
- Feedback
- Initiative
- Disciplinary deductions
- Overall performance score
- Employee KPI history
- Department KPI analysis

The dashboard can dynamically calculate company and employee performance metrics from live Odoo records.

### KPI Concept

The project uses weighted performance components together with applicable deductions.

Example conceptual model:

```text
Overall KPI
     │
     ├── Task Completion
     ├── Attendance
     ├── Training
     ├── Feedback
     ├── Initiative
     │
     └── Disciplinary Deductions
              │
              ▼
        Final KPI Score
