# -*- coding: utf-8 -*-
{
    'name': 'Smart Employee Performance & Promotion Management System',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Performance',
    'summary': 'AI-driven employee performance tracking, multi-level promotions, and 7 role-based OWL dashboards',
    'description': """
Smart Employee Performance & Promotion Management System for Odoo 19
====================================================================
* Goal Lifecycle Management (Draft -> Submitted -> TL Approved -> Manager Approved -> Active -> Completed)
* Strict Mathematical KPI Engine with Disciplinary Deductions
* Disciplinary Warning Engine with Promotion Blocking
* 5-Rule Promotion Eligibility Verification with AI Recommendations
* 7 Dedicated Role-Based OWL Dashboards (CEO, HR, Manager, Team Leader, Employee, AI Analytics, Reports)
* Configurable Dual AI Engine (OpenAI / Local LLM)
* Native QWeb PDF, XLSX, and CSV Reports
    """,
    'author': 'Enterprise Engineering Solutions',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'mail',
        'web',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/sequences.xml',
        'data/cron.xml',
        'views/res_config_settings_views.xml',
        'views/hr_employee_views.xml',
        'views/employee_goal_views.xml',
        'views/employee_kpi_views.xml',
        'views/performance_review_views.xml',
        'views/promotion_views.xml',
        'views/warning_views.xml',
        'views/reward_views.xml',
        'views/training_views.xml',
        'views/skill_matrix_views.xml',
        'views/career_path_views.xml',
        'views/menus.xml',
        'report/report_actions.xml',
        'report/report_templates.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'smart_employee_performance_management/static/src/scss/performance_dashboard.scss',
            'smart_employee_performance_management/static/src/components/kpi_card/kpi_card.js',
            'smart_employee_performance_management/static/src/components/kpi_card/kpi_card.xml',
            'smart_employee_performance_management/static/src/components/ai_chat/ai_chat.js',
            'smart_employee_performance_management/static/src/components/ai_chat/ai_chat.xml',
            'smart_employee_performance_management/static/src/dashboards/main_dashboard.js',
            'smart_employee_performance_management/static/src/dashboards/main_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}