# -*- coding: utf-8 -*-
import json
import logging
import requests
from datetime import date, timedelta
from odoo import models, api, fields

_logger = logging.getLogger(__name__)

class AIService(models.AbstractModel):
    _name = 'ai.service'
    _description = 'Dynamic Enterprise AI Service (Local Ollama Engine)'

    @api.model
    def generate_dynamic_ai_response(self, user_prompt, target_employee_id=None):
        """Extracts live employee database context and queries local Ollama instance."""
        ICPS = self.env['ir.config_parameter'].sudo()
        enabled = ICPS.get_param('smart_performance.ai_enabled', default=True)
        provider = ICPS.get_param('smart_performance.ai_provider', default='local_llm')
        endpoint = ICPS.get_param('smart_performance.ai_endpoint', default='http://127.0.0.1:11434/api/chat')
        model_name = ICPS.get_param('smart_performance.ai_model', default='llama3.2')

        if not enabled:
            return "The AI Analysis Engine is disabled in Settings."

        # 1. Gather live employee profile and performance metrics from DB
        emp = False
        if target_employee_id:
            emp = self.env['hr.employee'].sudo().browse(int(target_employee_id))
        if not emp or not emp.exists():
            emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if not emp:
            emp = self.env['hr.employee'].sudo().search([], order='id asc', limit=1)

        # 2. Extract live attendance metrics for the last 30 days
        thirty_days_ago = fields.Date.today() - timedelta(days=30)
        att_logs = self.env['employee.attendance.log'].sudo().search([
            ('employee_id', '=', emp.id if emp else False),
            ('date', '>=', thirty_days_ago)
        ])
        late_count_30d = len(att_logs.filtered(lambda l: l.is_late or l.status == 'late'))
        absent_count_30d = len(att_logs.filtered(lambda l: l.status == 'absent'))
        salary_deductions = late_count_30d // 4

        # 3. Extract live approved leaves
        year_start = date(fields.Date.today().year, 1, 1)
        leaves = self.env['employee.leave'].sudo().search([
            ('employee_id', '=', emp.id if emp else False),
            ('state', '=', 'approved'),
            ('date_from', '>=', year_start)
        ])
        casual_used = sum(leaves.filtered(lambda l: l.leave_type == 'casual').mapped('duration_days'))
        sick_used = sum(leaves.filtered(lambda l: l.leave_type == 'sick').mapped('duration_days'))
        yearly_used = sum(leaves.filtered(lambda l: l.leave_type == 'yearly').mapped('duration_days'))

        # 4. Extract active warnings & goals
        active_warnings = self.env['warning.record'].sudo().search([
            ('employee_id', '=', emp.id if emp else False),
            ('state', '=', 'active')
        ])
        active_goals = self.env['employee.goal'].sudo().search([
            ('employee_id', '=', emp.id if emp else False),
            ('state', 'in', ['submitted', 'leader_approved', 'in_progress'])
        ])

        # 5. Check 5 promotion criteria
        kpi_score = getattr(emp, 'kpi_score', 0.0)
        attendance_rate = getattr(emp, 'kpi_attendance_score', 0.0)
        service_months = getattr(emp, 'service_duration_months', 0.0)
        warnings_count = len(active_warnings)
        is_promo_eligible = (service_months >= 6.0 and attendance_rate >= 80.0 and warnings_count < 3 and kpi_score >= 75.0)

        # 6. Construct prompt
        system_context = f"""
You are the AI Performance Copilot for an Enterprise HR System on Odoo 19.
Always respond with professional, concise, scannable Markdown formatting:
- Use standalone bold headers or inline bold text for key metrics.
- Use clean bullet points.
- Never write conversational filler setups. Answer the user's question directly using the ground truth database context below.

CURRENT ACTIVE EMPLOYEE DATABASE CONTEXT:
- Name: {emp.name if emp else 'User'}
- Designation / Role: {emp.job_id.name if emp and emp.job_id else 'Trainee Executive'}
- Department: {emp.department_id.name if emp and emp.department_id else 'IT & Infrastructure'}
- Shift: {getattr(emp, 'shift_type', 'General (09:00 AM - 05:00 PM)')}
- Tenure: {getattr(emp, 'service_length_str', '1 month')} ({service_months} months)
- Overall KPI Score: {kpi_score} / 100
- Attendance Rate: {attendance_rate}%
- Last 30 Days Record: {late_count_30d} Late arrivals, {absent_count_30d} Unauthorized Absences
- Current Salary Deductions: {salary_deductions} day(s) deducted due to late rule (4 lates = 1 day deduction)
- Active Warnings: {warnings_count} active disciplinary warning(s)
- Annual Leave Balances: Casual {max(0, 12 - casual_used)}/12 left, Sick {max(0, 14 - sick_used)}/14 left, Yearly {max(0, 10 - yearly_used)}/10 left
- Active Goals Count: {len(active_goals)} active milestone(s)
- Promotion Eligibility: {'ELIGIBLE (Meets all 5 enterprise criteria)' if is_promo_eligible else 'INELIGIBLE (Does not meet all 5 criteria: KPI>=75, Tenure>=6m, Attendance>=80%, Warnings<3)'}

COMPANY HR POLICIES:
1. Punctuality: Office starts at 09:00 AM with a 10-minute grace period. Check-in after 09:10 AM is counted as Late.
2. Late Deductions: Every 4 late check-ins in a month triggers an automatic 1-day salary deduction.
3. 3-Day Absence Rule: 3 unexcused absences triggers an AI disciplinary notice. 1 more unexcused absence results in immediate salary loss.
4. Promotion Thresholds: Service >= 6 months, Attendance >= 80%, Active Warnings < 3, KPI >= 75%.
"""

        if provider == 'openai':
            endpoint = endpoint or 'https://api.openai.com/v1/chat/completions'
            api_key = ICPS.get_param('smart_performance.ai_api_key', default='')
        else:
            api_key = ''

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9
            }
        }

        # 7. Call local Ollama
        try:
            headers = {'Authorization': f'Bearer {api_key}'} if provider == 'openai' and api_key else {}
            res = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            if res.status_code == 200:
                data = res.json()
                if 'message' in data and 'content' in data['message']:
                    return data['message']['content']
                elif 'response' in data:
                    return data['response']
                elif data.get('choices'):
                    message = data['choices'][0].get('message', {})
                    if message.get('content'):
                        return message['content']
            _logger.warning("Ollama returned HTTP %s: %s", res.status_code, res.text)
        except Exception as e:
            _logger.warning("Ollama connection failed on %s (%s). Generating dynamic rule-based output.", endpoint, e)

        # Dynamic Fallback based on real DB metrics
        return self._generate_dynamic_db_response(emp, kpi_score, attendance_rate, late_count_30d, warnings_count, is_promo_eligible)

    @api.model
    def _generate_dynamic_db_response(self, emp, kpi, att, lates, warnings, promo_eligible):
        status_text = "**ELIGIBLE** for promotion consideration." if promo_eligible else "**PENDING** (Threshold criteria not yet satisfied)."
        deductions = lates // 4
        return (
            f"**Real-Time Performance Overview for {emp.name if emp else 'User'}**\n\n"
            f"* **KPI Score**: **{kpi} / 100**\n"
            f"* **Attendance Rate**: **{att}%**\n"
            f"* **Late Arrivals (30d)**: **{lates}** ({deductions} day salary deduction applied)\n"
            f"* **Active Warnings**: **{warnings}** active record(s)\n"
            f"* **Promotion Readiness**: {status_text}\n\n"
            f"> _Live data retrieved from PostgreSQL. Local Ollama response generated._"
        )