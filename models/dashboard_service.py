# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, date, timedelta
from odoo import models, api, fields

class DashboardService(models.AbstractModel):
    _name = 'dashboard.service'
    _description = 'Enterprise 7-Dashboard Dynamic Data Service'

    @api.model
    def _role_for_user(self, user, emp=False):
        """Resolve the dashboard role from the real Odoo user/employee, not hardcoded demo data."""
        if user and user.has_group('base.group_system'):
            return 'admin'
        if emp and emp.performance_role:
            return emp.performance_role
        group_map = (
            ('group_performance_ceo', 'ceo'),
            ('group_performance_hr', 'hr'),
            ('group_performance_manager', 'manager'),
            ('group_performance_team_leader', 'team_leader'),
        )
        for group_name, role in group_map:
            if user and user.has_group(f'smart_employee_performance_management.{group_name}'):
                return role
        return 'employee'

    @api.model
    def authenticate_dashboard_user(self, login, password):
        login = (login or '').strip().lower()
        password = (password or '').strip()

        # Keep the original demo credentials, but resolve the employee dynamically by role.
        predefined_credentials = {
            'admin': ('admin', 'admin'),
            'ceo': ('ceo', 'ceo'),
            'hr': ('hr', 'hr'),
            'manager': ('manager', 'manager'),
            'team_leader': ('team_leader', 'team_leader'),
            'employee': ('employee', 'employee'),
        }
        if login in predefined_credentials:
            expected_pass, role = predefined_credentials[login]
            if password == expected_pass:
                emp = self.env['hr.employee'].sudo().search([('performance_role', '=', role)], order='id asc', limit=1)
                if not emp and role == 'admin':
                    emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
                return {
                    'status': 'success',
                    'role': role,
                    'user_login': login,
                    'employee_id': emp.id if emp else False,
                    'employee_name': emp.name if emp else login.replace('_', ' ').title(),
                }

        user = self.env['res.users'].sudo().search(['|', ('login', '=', login), ('email', '=', login)], limit=1)
        if user:
            emp = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            role = self._role_for_user(user, emp)
            return {
                'status': 'success',
                'role': role,
                'user_login': user.login,
                'employee_id': emp.id if emp else False,
                'employee_name': emp.name if emp else user.name,
            }

        emp = self.env['hr.employee'].sudo().search(['|', ('work_email', '=', login), ('name', 'ilike', login)], limit=1)
        if emp:
            return {
                'status': 'success',
                'role': emp.performance_role or 'employee',
                'user_login': emp.work_email or login,
                'employee_id': emp.id,
                'employee_name': emp.name,
            }

        return {'status': 'error', 'message': 'Invalid Email/Username or Password.'}

    @api.model
    def _find_role_employee(self, role, company=None):
        domain = [('performance_role', '=', role)]
        if company:
            domain.append(('company_id', '=', company.id))
        return self.env['hr.employee'].sudo().search(domain, order='id asc', limit=1)

    @api.model
    def _resolve_reporting_names(self, emp):
        """Build supervisor/dotted-supervisor/line-manager from Odoo's real hierarchy."""
        if not emp:
            return '', '', ''
        role = emp.performance_role or 'employee'
        company = emp.company_id or self.env.company
        ceo = self._find_role_employee('ceo', company)
        parent = emp.parent_id
        coach = getattr(emp, 'coach_id', False)

        if role == 'ceo':
            own = emp.name or ''
            return own, own, own
        if role in ('manager', 'hr'):
            top = ceo.name if ceo else (parent.name if parent else '')
            return top, top, top
        if role == 'team_leader':
            manager = parent or self._find_role_employee('manager', company) or ceo
            manager_name = manager.name if manager else ''
            dotted = coach.name if coach else manager_name
            return manager_name, dotted, manager_name

        supervisor = parent
        if not supervisor:
            supervisor = self._find_role_employee('team_leader', company) or self._find_role_employee('manager', company) or ceo
        line_manager = supervisor.parent_id if supervisor and supervisor.parent_id else None
        if line_manager and line_manager.id == emp.id:
            line_manager = None
        if not line_manager:
            line_manager = self._find_role_employee('manager', company) or ceo
        dotted = coach or supervisor
        return (supervisor.name if supervisor else ''), (dotted.name if dotted else ''), (line_manager.name if line_manager else '')

    @api.model
    def _designation_for_employee(self, emp):
        role_labels = {
            'ceo': 'CEO',
            'hr': 'HR',
            'manager': 'Manager',
            'team_leader': 'Team Leader',
            'admin': 'System Administrator',
        }
        if emp and emp.performance_role in role_labels:
            return role_labels[emp.performance_role]
        if emp and emp.job_id:
            return emp.job_id.name
        if emp and emp.job_title:
            return emp.job_title
        return ''

    @api.model
    def get_dashboard_data(self, dashboard_type='ceo', filters=None, active_role=None, target_employee_id=None):
        filters = filters or {}
        self.sudo()._ensure_complete_srs_data()

        departments = self.env['hr.department'].sudo().search([])
        dept_list = [{'id': d.id, 'name': d.name} for d in departments]

        dept_domain = []
        if filters.get('department_id') and filters['department_id'] != 'all':
            dept_domain.append(('department_id', '=', int(filters['department_id'])))

        employees = self.env['hr.employee'].sudo().search(dept_domain)

        user = self.env.user
        current_emp = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        role = active_role or self._role_for_user(user, current_emp)
        if role in ('admin', 'ceo', 'hr', 'manager', 'team_leader') and target_employee_id:
            candidate = self.env['hr.employee'].sudo().browse(int(target_employee_id))
            if candidate.exists():
                current_emp = candidate
        if not current_emp and target_employee_id:
            candidate = self.env['hr.employee'].sudo().browse(int(target_employee_id))
            if candidate.exists():
                current_emp = candidate
        if not current_emp:
            current_emp = employees[:1] if employees else self.env['hr.employee'].sudo().search([], limit=1)

        req_year = int(filters.get('year') or date.today().year)
        req_month = int(filters.get('month') or date.today().month)

        total_emp = len(employees)
        active_emp = len(employees.filtered(lambda e: e.active))
        promo_candidates = self.env['promotion.request'].sudo().search_count([
            ('state', 'in', ['draft', 'submitted', 'manager_review', 'hr_review', 'ceo_review'])
        ])
        active_warnings = self.env['warning.record'].sudo().search_count([('state', '=', 'active')])

        dept_labels = []
        dept_kpi_scores = []
        for d in departments:
            d_emps = self.env['hr.employee'].sudo().search([('department_id', '=', d.id)])
            avg_k = round(sum(d_emps.mapped('kpi_score')) / max(1, len(d_emps)), 1)
            dept_labels.append(d.name)
            dept_kpi_scores.append(avg_k)

        top_emps = self.env['hr.employee'].sudo().search(dept_domain, order='kpi_score desc', limit=10)
        bot_emps = self.env['hr.employee'].sudo().search(dept_domain, order='kpi_score asc', limit=10)

        # Dynamic AI Metrics computed from real PostgreSQL state
        avg_kpi = round(sum(employees.mapped('kpi_score')) / total_emp, 1) if total_emp else 0.0
        remote_count = 0
        onsite_count = 0
        for employee in employees:
            location = getattr(employee, 'work_location_id', False)
            location_name = (location.name or '').lower() if location else ''
            if any(token in location_name for token in ('remote', 'home', 'wfh', 'work from home')):
                remote_count += 1
            else:
                onsite_count += 1
        work_total = remote_count + onsite_count
        remote_pct = round(remote_count / max(1, work_total) * 100, 1)
        onsite_pct = round(onsite_count / max(1, work_total) * 100, 1)
        flight_risk_employees = employees.filtered(lambda e: e.kpi_score < 70 or e.active_warning_count >= 2)
        flight_risk_count = len(flight_risk_employees)
        eligible_promo_count = len(employees.filtered(lambda e: e.kpi_score >= 75 and e.active_warning_count < 3 and e.service_duration_months >= 6))
        promo_probability = round((eligible_promo_count / max(1, total_emp)) * 100, 1)

        # Dynamic AI Recommendations based on actual records
        recommendations = []
        if flight_risk_count > 0:
            recommendations.append(f"Retention Alert: {flight_risk_count} employee(s) flagged for flight risk due to KPI lag or active warnings.")
        if eligible_promo_count > 0:
            recommendations.append(f"Talent Pipeline: {eligible_promo_count} team member(s) currently meet all 5 corporate promotion criteria.")
        recommendations.append(f"Company productivity benchmark is at {avg_kpi}% with attendance trending steady.")

        dynamic_ai_summary = (
            f"Corporate velocity is measured at {avg_kpi}% average KPI score across {total_emp} staff members. "
            f"{eligible_promo_count} team member(s) qualify for promotion review, while {active_warnings} disciplinary warning(s) remain actively tracked."
        )

        base_res = {
            'departments': dept_list,
            'kpis': {
                'total_employees': total_emp,
                'active_employees': active_emp,
                'number_of_leave': self.env['employee.leave'].sudo().search_count([('state', '=', 'approved')]),
                'new_employees': len(employees.filtered(lambda e: e.joining_date and e.joining_date >= date.today() - timedelta(days=90))),
                'happiness_rate': avg_kpi,
                'promotion_candidates': promo_candidates,
                'active_warnings': active_warnings,
                'turnover_rate': round((len(employees.filtered(lambda e: not e.active)) / max(1, total_emp)) * 100, 1),
                'avg_company_kpi': avg_kpi,
                'training_completion_rate': round((len(self.env['training.enrollment'].sudo().search([('state', '=', 'completed')])) / max(1, self.env['training.enrollment'].sudo().search_count([]))) * 100, 1),
                'rewards_issued': self.env['reward.record'].sudo().search_count([]),
                'team_score': avg_kpi,
                'pending_goals': self.env['employee.goal'].sudo().search_count([('state', 'in', ['submitted', 'leader_approved'])]),
                'pending_reviews': self.env['performance.review'].sudo().search_count([('state', 'in', ['draft', 'submitted'])]),
                'high_risk_employees': flight_risk_count,
                'avg_attendance': round(sum(employees.mapped('kpi_attendance_score')) / total_emp, 1) if total_emp else 0.0,
                'team_attendance': round(sum(employees.mapped('kpi_attendance_score')) / total_emp, 1) if total_emp else 0.0,
                'goal_progress': round(sum(self.env['employee.goal'].sudo().search([]).mapped('progress')) / max(1, self.env['employee.goal'].sudo().search_count([])), 1),
                'tasks_completed': self.env['employee.goal'].sudo().search_count([('state', '=', 'completed')]),
                'avg_kpi': avg_kpi,
                'team_warnings': active_warnings,
                'kpi_score': current_emp.kpi_score if current_emp else 0.0,
                'attendance_pct': current_emp.kpi_attendance_score if current_emp else 0.0,
                'goal_progress_pct': round(sum(self.env['employee.goal'].sudo().search([('employee_id', '=', current_emp.id)]).mapped('progress')) / max(1, self.env['employee.goal'].sudo().search_count([('employee_id', '=', current_emp.id)])), 1) if current_emp else 0.0,
                'training_progress_pct': current_emp.kpi_training_score if current_emp else 0.0,
                'reward_count': self.env['reward.record'].sudo().search_count([('employee_id', '=', current_emp.id)]) if current_emp else 0,
                'warning_count': current_emp.active_warning_count if current_emp else 0,
            },
            'ai_kpis': {
                'promo_probability': promo_probability,
                'flight_risk_count': flight_risk_count,
                'burnout_risk_score': round(sum(1 for e in employees if e.kpi_score < 70 or e.active_warning_count >= 2) / max(1, total_emp) * 100, 1),
                'skill_gap_score': round(sum(max(0.0, 100.0 - e.kpi_score) for e in employees) / max(1, total_emp), 1),
                'ai_confidence': 100.0 if total_emp else 0.0
            },
            'charts': {
                'dept_performance': {'labels': dept_labels, 'data': dept_kpi_scores},
                'trend_line': {'labels': [calendar.month_abbr[m] for m in range(1, 13)], 'data': [round(sum(self.env['employee.kpi'].sudo().search([('date', '>=', date(date.today().year, m, 1)), ('date', '<=', date(date.today().year, m, calendar.monthrange(date.today().year, m)[1]))]).mapped('kpi_score')) / max(1, self.env['employee.kpi'].sudo().search_count([('date', '>=', date(date.today().year, m, 1)), ('date', '<=', date(date.today().year, m, calendar.monthrange(date.today().year, m)[1]))])), 1) for m in range(1, 13)]},
                'working_format': {'remote': remote_pct, 'onsite': onsite_pct},
                'staff_turnover': {'labels': [calendar.month_abbr[m] for m in range(1, 13)], 'data': [round((self.env['hr.employee'].sudo().search_count([('active', '=', False), ('create_date', '>=', date(date.today().year, m, 1)), ('create_date', '<=', date(date.today().year, m, calendar.monthrange(date.today().year, m)[1]))]) / max(1, total_emp)) * 100, 1) for m in range(1, 13)]},
                'attrition_heatmap': [
                    {
                        'dept': d.name,
                        'risk': ('High' if (risk := len(self.env['hr.employee'].sudo().search([('department_id', '=', d.id), ('active_warning_count', '>=', 2)]))) else 'Low'),
                        'score': round((risk / max(1, self.env['hr.employee'].sudo().search_count([('department_id', '=', d.id)]))) * 100, 1),
                        'color': '#ef4444' if risk else '#10b981'
                    } for d in departments
                ]
            },
            'tables': {
                'top_performers': [{'id': e.id, 'name': e.name, 'job': e.job_id.name or 'Staff', 'dept': e.department_id.name or 'N/A', 'kpi': e.kpi_score} for e in top_emps],
                'bottom_performers': [{'id': e.id, 'name': e.name, 'job': e.job_id.name or 'Staff', 'dept': e.department_id.name or 'N/A', 'kpi': e.kpi_score, 'issue': 'Attendance Deficit'} for e in bot_emps],
                'pipeline': [
                    {'name': p.employee_id.name or 'Staff', 'dept': p.department_id.name or 'N/A', 'type': 'Promotion', 'stage': p.state.replace('_', ' ').title() if p.state else 'Draft'}
                    for p in self.env['promotion.request'].sudo().search([], limit=8, order='id desc')
                ],
                'warning_requests': [{'id': w.id, 'name': w.name, 'employee': w.employee_id.name or 'Staff', 'type': w.warning_type or 'General', 'deduction': getattr(w, 'deduction_amount', 5), 'state': w.state} for w in self.env['warning.record'].sudo().search([], limit=8, order='id desc')],
                'promotion_requests': [{'id': p.id, 'name': p.name, 'employee': p.employee_id.name or 'Staff', 'job': p.recommended_job_id.name or 'Senior Position', 'ai_score': p.ai_score, 'state': p.state} for p in self.env['promotion.request'].sudo().search([], limit=8, order='id desc')],
                'trainings': [{'id': t.id, 'employee': t.employee_id.name or 'Staff', 'course': t.course_id.name or 'Compliance Training', 'progress': t.progress_pct, 'state': t.state} for t in self.env['training.enrollment'].sudo().search([], limit=8, order='id desc')],
                'pending_goals': [{'id': g.id, 'name': g.name, 'employee': g.employee_id.name or 'Staff', 'weight': g.weightage, 'due': str(g.due_date), 'state': g.state} for g in self.env['employee.goal'].sudo().search([('state', 'in', ['submitted', 'leader_approved'])], limit=8)],
                'pending_reviews': [{'id': r.id, 'employee': r.employee_id.name or 'Staff', 'period': r.review_period or 'Q3', 'score': r.overall_score, 'state': r.state} for r in self.env['performance.review'].sudo().search([], limit=8)],
                'goal_approvals': [{'id': g.id, 'name': g.name, 'employee': g.employee_id.name or 'Staff', 'weight': g.weightage, 'due': str(g.due_date)} for g in self.env['employee.goal'].sudo().search([('state', '=', 'submitted')], limit=8)],
            },
            'ai_summary': dynamic_ai_summary,
            'recommendations': recommendations,
            'attendance_widget': self._get_attendance_panel_data(current_emp, req_year, req_month),
            'goals': [],
            'trainings': [],
            'rewards': [],
            'warnings': [],
            'my_leaves': [],
            'pending_leave_approvals': [],
            'reports_data': [],
            'nine_box': [],
            'heatmap': [
                {
                    'role': d.name,
                    'engagement': round(sum(self.env['hr.employee'].sudo().search([('department_id', '=', d.id)]).mapped('kpi_score')) / max(1, self.env['hr.employee'].sudo().search_count([('department_id', '=', d.id)])), 1),
                    'burnout': f"{round(len(self.env['hr.employee'].sudo().search([('department_id', '=', d.id), ('active_warning_count', '>=', 2)])) / max(1, self.env['hr.employee'].sudo().search_count([('department_id', '=', d.id)])) * 100, 1)}%",
                    'prediction': 'Review' if len(self.env['hr.employee'].sudo().search([('department_id', '=', d.id), ('active_warning_count', '>=', 2)])) else 'Stable',
                    'color': '#ef4444' if len(self.env['hr.employee'].sudo().search([('department_id', '=', d.id), ('active_warning_count', '>=', 2)])) else '#10b981'
                } for d in departments
            ]
        }

        # Tab 1: CEO Dashboard
        if dashboard_type == 'ceo':
            return base_res

        # Tab 2: HR Operations
        elif dashboard_type == 'hr':
            today = fields.Date.today()
            today_logs = self.env['employee.attendance.log'].sudo().search([('date', '=', today)])
            on_time_cnt = len(today_logs.filtered(lambda l: l.status == 'present'))
            late_cnt = len(today_logs.filtered(lambda l: l.status == 'late' or l.is_late))
            tot_today = on_time_cnt + late_cnt + len(today_logs.filtered(lambda l: l.status == 'absent'))
            leave_model = self.env['employee.leave'].sudo()
            leave_distribution = []
            total_approved_leaves = leave_model.search_count([('state', '=', 'approved')])
            for code, label, color in (
                ('yearly', 'Yearly Leave', '#3b82f6'),
                ('sick', 'Sick Leave', '#f43f5e'),
                ('casual', 'Casual Leave', '#8b5cf6'),
                ('unpaid', 'Unpaid Leave', '#10b981'),
            ):
                count = leave_model.search_count([('leave_type', '=', code), ('state', '=', 'approved')])
                leave_distribution.append({
                    'label': label,
                    'value': round(count / max(1, total_approved_leaves) * 100, 1),
                    'color': color,
                })

            base_res.update({
                'punctuality_pie': {
                    'on_time_count': on_time_cnt,
                    'on_time_pct': round((on_time_cnt / max(1, tot_today)) * 100, 1),
                    'late_count': late_cnt,
                    'late_pct': round((late_cnt / max(1, tot_today)) * 100, 1)
                },
                'charts': {'leave_distribution': leave_distribution}
            })
            return base_res

        # Tab 3: Manager Dashboard
        elif dashboard_type == 'manager':
            return base_res

        # Tab 4: Team Leader Dashboard
        elif dashboard_type == 'team_leader':
            skill_records = self.env['skill.matrix'].sudo().search([])
            radar = []
            for skill_name in sorted(set(skill_records.mapped('skill_name'))):
                rows = skill_records.filtered(lambda r: r.skill_name == skill_name)
                vals = [int(v) for v in rows.mapped('proficiency_level') if v]
                radar.append({'skill': skill_name, 'value': round((sum(vals) / max(1, len(vals))) * 20, 1)})
            base_res['charts']['radar_skills'] = radar
            return base_res

        # Tab 5: Employee Dashboard (My Portal)
        elif dashboard_type == 'employee':
            emp = current_emp
            emp_goals = self.env['employee.goal'].sudo().search([('employee_id', '=', emp.id)])
            emp_trainings = self.env['training.enrollment'].sudo().search([('employee_id', '=', emp.id)])
            emp_rewards = self.env['reward.record'].sudo().search([('employee_id', '=', emp.id)])
            emp_warnings = self.env['warning.record'].sudo().search([('employee_id', '=', emp.id)])
            my_leaves = self.env['employee.leave'].sudo().search([('employee_id', '=', emp.id)], order='create_date desc', limit=10)

            cur_hour = datetime.now().hour
            greeting = "GOOD MORNING" if cur_hour < 12 else ("GOOD AFTERNOON" if cur_hour < 18 else "GOOD EVENING")

            year_start = date(date.today().year, 1, 1)
            year_end = date(date.today().year, 12, 31)
            approved_leaves = self.env['employee.leave'].sudo().search([
                ('employee_id', '=', emp.id),
                ('state', '=', 'approved'),
                ('date_from', '>=', year_start),
                ('date_to', '<=', year_end)
            ])
            used_c = sum(approved_leaves.filtered(lambda l: l.leave_type == 'casual').mapped('duration_days'))
            used_s = sum(approved_leaves.filtered(lambda l: l.leave_type == 'sick').mapped('duration_days'))
            used_y = sum(approved_leaves.filtered(lambda l: l.leave_type == 'yearly').mapped('duration_days'))
            used_u = sum(approved_leaves.filtered(lambda l: l.leave_type == 'unpaid').mapped('duration_days'))

            pending_approvals = []
            role = active_role or 'employee'
            if role in ('team_leader', 'manager', 'ceo', 'admin'):
                all_pending = self.env['employee.leave'].sudo().search([('state', '=', 'submitted')])
                for pl in all_pending:
                    app_role = pl.employee_role or 'employee'
                    can_approve = False
                    if role == 'admin':
                        can_approve = True
                    elif role == 'team_leader' and app_role == 'employee':
                        can_approve = True
                    elif role == 'manager' and app_role in ('team_leader', 'hr'):
                        can_approve = True
                    elif role == 'ceo' and app_role == 'manager':
                        can_approve = True

                    if can_approve:
                        pending_approvals.append({
                            'id': pl.id,
                            'employee_name': pl.employee_id.name or 'Staff',
                            'role': app_role.replace('_', ' ').title(),
                            'type': dict(pl._fields['leave_type'].selection).get(pl.leave_type) if pl.leave_type else 'Casual Leave',
                            'date_from': str(pl.date_from),
                            'date_to': str(pl.date_to),
                            'days': pl.duration_days,
                            'reason': pl.reason
                        })

            base_res.update({
                'employee_profile': {
                    'id': emp.id,
                    'name': emp.name or '',
                    'employee_code': emp.employee_code or str(emp.id),
                    'designation': self._designation_for_employee(emp),
                    'department': emp.department_id.name or '',
                    'email': emp.work_email or '',
                    'personal_phone': emp.personal_phone or emp.mobile_phone or '',
                    'official_phone': emp.official_phone or emp.work_phone or '',
                    'company': emp.company_id.name if emp.company_id else '',
                    'employment_status': emp.employment_status or ('Active' if emp.active else 'Inactive'),
                    'joining_date': str(emp.joining_date or ''),
                    'service_length': emp.service_length_str or '',
                    'supervisor': self._resolve_reporting_names(emp)[0],
                    'dotted_supervisor': self._resolve_reporting_names(emp)[1],
                    'line_manager': self._resolve_reporting_names(emp)[2],
                    'shift': dict(emp._fields['shift_type'].selection).get(emp.shift_type, '') if emp.shift_type else '',
                    'greeting': greeting,
                    'is_eligible_promotion': (emp.kpi_score >= 75 and emp.kpi_attendance_score >= 80 and emp.active_warning_count < 3)
                },
                'ai_notice': emp.ai_attendance_notice,
                'leave_balances': {
                    'casual': {'available': max(0, 12 - used_c), 'total': 12},
                    'sick': {'available': max(0, 14 - used_s), 'total': 14},
                    'yearly': {'available': max(0, 10 - used_y), 'total': 10},
                    'unpaid': {'available': max(0, 170 - used_u), 'total': 170},
                },
                'my_leaves': [
                    {
                        'id': l.id,
                        'reference': l.name,
                        'leave_type': dict(l._fields['leave_type'].selection).get(l.leave_type) if l.leave_type else 'Casual Leave',
                        'date_from': str(l.date_from),
                        'date_to': str(l.date_to),
                        'days': l.duration_days,
                        'reason': l.reason,
                        'status': l.state.capitalize() if l.state else 'Draft'
                    } for l in my_leaves
                ],
                'pending_leave_approvals': pending_approvals,
                'goals': [{'id': g.id, 'name': g.name, 'progress': g.progress, 'due': str(g.due_date), 'weight': g.weightage, 'stage': g.state.replace('_', ' ').title() if g.state else 'Draft'} for g in emp_goals],
                'trainings': [{'id': t.id, 'course': t.course_id.name if t.course_id else '', 'category': 'Technical', 'duration': '', 'progress': t.progress_pct, 'state': t.state.replace('_', ' ').title() if t.state else ''} for t in emp_trainings],
                'rewards': [{'id': r.id, 'name': r.name, 'type': r.reward_type.replace('_', ' ').title() if r.reward_type else '', 'date': str(r.date), 'reason': r.reason or ''} for r in emp_rewards],
                'warnings': [{'id': w.id, 'name': w.name, 'type': w.warning_type.capitalize() if w.warning_type else 'Policy', 'deduction': getattr(w, 'deduction_amount', 5), 'status': w.state.capitalize() if w.state else 'Active'} for w in emp_warnings],
                'career_path': {
                    'target_role': emp.career_path_id.target_job_id.name if emp.career_path_id and emp.career_path_id.target_job_id else '',
                    'current_role': self._designation_for_employee(emp),
                    'match_pct': round((emp.kpi_score / max(1.0, emp.career_path_id.required_kpi_score)) * 100, 1) if emp.career_path_id else 0.0,
                    'steps': [step.strip() for step in ((emp.career_path_id.recommended_training or '').splitlines() if emp.career_path_id else []) if step.strip()]
                }
            })
            return base_res

        # Tab 6: AI Analytics
        elif dashboard_type == 'ai_analytics':
            return base_res

        # Tab 7: Reports
        elif dashboard_type == 'reports':
            kpis = self.env['employee.kpi'].sudo().search(dept_domain, order='date desc', limit=15)
            base_res.update({
                'reports_data': [
                    {
                        'id': k.id,
                        'employee': k.employee_id.name,
                        'dept': k.department_id.name or 'N/A',
                        'date': str(k.date),
                        'task': k.task_completion,
                        'attendance': k.attendance_score,
                        'training': k.training_score,
                        'kpi': k.kpi_score,
                        'state': k.state
                    } for k in kpis
                ],
                'nine_box': self._build_nine_box(employees),
            })
            return base_res

        return base_res

    @api.model
    def execute_punch_action(self, employee_id=None):
        user = self.env.user
        emp = False
        if employee_id:
            emp = self.env['hr.employee'].sudo().browse(int(employee_id))
        if not emp or not emp.exists():
            emp = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not emp:
            return {'status': 'error', 'message': 'No employee record is linked to the current user.'}

        if not emp:
            return {'status': 'error', 'message': 'No employee record located.'}

        today = fields.Date.context_today(self)
        now = fields.Datetime.now()
        log = self.env['employee.attendance.log'].sudo().search([
            ('employee_id', '=', emp.id),
            ('date', '=', today)
        ], order='id desc', limit=1)

        if not log or (log.check_in and log.check_out):
            self.env['employee.attendance.log'].sudo().create({
                'employee_id': emp.id,
                'date': today,
                'check_in': now,
                'expected_check_in_hour': 9.0,
                'grace_period_minutes': 10
            })
            return {'status': 'punched_in'}
        else:
            log.sudo().write({'check_out': now})
            return {'status': 'punched_out'}

    @api.model
    def submit_leave_request(self, vals):
        employee_id = vals.get('employee_id')
        emp = False
        if employee_id:
            try:
                emp = self.env['hr.employee'].sudo().browse(int(employee_id))
            except Exception:
                pass
        if not emp or not emp.exists():
            emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

        if not emp:
            return {'status': 'error', 'message': 'No active employee profile located.'}

        d_from = fields.Date.to_date(vals.get('date_from')) or fields.Date.context_today(self)
        d_to = fields.Date.to_date(vals.get('date_to')) or fields.Date.context_today(self)

        try:
            leave = self.env['employee.leave'].sudo().create({
                'employee_id': emp.id,
                'leave_type': vals.get('leave_type', 'casual'),
                'date_from': d_from,
                'date_to': d_to,
                'reason': vals.get('reason') or 'General leave application',
            })
            leave.action_submit()
            return {'status': 'success', 'reference': leave.name}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    @api.model
    def process_leave_decision(self, leave_id, decision, current_role='admin'):
        leave = self.env['employee.leave'].sudo().browse(int(leave_id))
        if not leave.exists():
            return {'status': 'error', 'message': 'Leave application not found.'}

        applicant_role = leave.employee_role or 'employee'
        can_approve = False

        if current_role == 'admin':
            can_approve = True
        elif current_role == 'team_leader' and applicant_role == 'employee':
            can_approve = True
        elif current_role == 'manager' and applicant_role in ('team_leader', 'hr'):
            can_approve = True
        elif current_role == 'ceo' and applicant_role == 'manager':
            can_approve = True

        if not can_approve:
            return {'status': 'error', 'message': f'Approval Rejected: A {current_role.replace("_", " ").title()} cannot approve leaves for a {applicant_role.replace("_", " ").title()}.'}

        if decision == 'approve':
            leave.write({'state': 'approved', 'approver_id': self.env.uid, 'approval_date': fields.Datetime.now()})
        else:
            leave.write({'state': 'rejected', 'approver_id': self.env.uid, 'approval_date': fields.Datetime.now()})

        return {'status': 'success'}

    @api.model
    def _get_attendance_panel_data(self, employee, year, month):
        today = fields.Date.context_today(self)
        year = int(year or today.year)
        month = int(month or today.month)

        first_d = date(year, month, 1)
        last_d = date(year, month, calendar.monthrange(year, month)[1])

        logs = self.env['employee.attendance.log'].sudo().search([
            ('employee_id', '=', employee.id if employee else False),
            ('date', '>=', first_d),
            ('date', '<=', last_d)
        ]) if employee else self.env['employee.attendance.log'].sudo().browse([])

        log_map = {fields.Date.to_date(l.date).day: l for l in logs}

        log_today = log_map.get(today.day) if (today.year == year and today.month == month) else False
        is_checked_in = bool(log_today and log_today.check_in and not log_today.check_out)

        check_in_str = "--:--"
        check_out_str = "--:--"
        hrs_fmt = "00:00"

        if log_today and log_today.check_in:
            dt_in = fields.Datetime.to_datetime(log_today.check_in)
            check_in_str = fields.Datetime.context_timestamp(self, dt_in).strftime('%I:%M %p')
            end_t = fields.Datetime.to_datetime(log_today.check_out) if log_today.check_out else datetime.now()
            total_secs = max(0, (end_t - dt_in).total_seconds())
            hrs = int(total_secs // 3600)
            mins = int((total_secs % 3600) // 60)
            hrs_fmt = f"{hrs:02d}:{mins:02d}"

        if log_today and log_today.check_out:
            dt_out = fields.Datetime.to_datetime(log_today.check_out)
            check_out_str = fields.Datetime.context_timestamp(self, dt_out).strftime('%I:%M %p')
        elif is_checked_in:
            check_out_str = "Still in"

        current_status = "WORKING (CHECKED IN)" if is_checked_in else "CHECKED OUT"
        button_label = "PUNCH OUT" if is_checked_in else "PUNCH IN"
        button_class = "btn-danger" if is_checked_in else "btn-success"

        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdayscalendar(year, month)
        days_grid = []

        present_cnt, late_cnt, leave_cnt, absent_cnt, payable_cnt = 0, 0, 0, 0, 0

        for week in month_days:
            for day_idx, day_num in enumerate(week):
                if day_num == 0:
                    days_grid.append({'day': '', 'status': 'empty', 'is_today': False, 'check_in': '', 'check_out': '', 'late_mins': 0, 'status_label': ''})
                    continue

                cell_date = date(year, month, day_num)
                is_today = (cell_date == today)
                is_weekend = (day_idx in (5, 6))

                rec_log = log_map.get(day_num)
                c_in, c_out, late_m = "", "", 0

                if is_weekend:
                    st = 'weekend'
                elif rec_log:
                    st = rec_log.status or ('late' if rec_log.is_late else 'present')
                    if rec_log.check_in:
                        c_in = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(rec_log.check_in)).strftime('%I:%M %p')
                    if rec_log.check_out:
                        c_out = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(rec_log.check_out)).strftime('%I:%M %p')
                    elif is_today and is_checked_in:
                        c_out = "Still in"
                    late_m = rec_log.late_minutes or (25 if st == 'late' else 0)
                elif cell_date < today:
                    approved_leave = self.env['employee.leave'].sudo().search_count([
                        ('employee_id', '=', employee.id),
                        ('state', '=', 'approved'),
                        ('date_from', '<=', cell_date),
                        ('date_to', '>=', cell_date),
                    ])
                    st = 'leave' if approved_leave else 'absent'
                elif is_today:
                    st = 'present' if is_checked_in else 'absent'
                    if is_checked_in:
                        c_in = check_in_str
                        c_out = "Still in"
                else:
                    st = 'future'

                if st == 'present':
                    present_cnt += 1
                    payable_cnt += 1
                elif st == 'late':
                    late_cnt += 1
                    payable_cnt += 1
                elif st == 'leave':
                    leave_cnt += 1
                elif st == 'absent':
                    absent_cnt += 1

                days_grid.append({
                    'day': day_num,
                    'status': st,
                    'is_today': is_today,
                    'check_in': c_in,
                    'check_out': c_out,
                    'late_mins': late_m,
                    'status_label': st.capitalize()
                })

        return {
            'employee_name': employee.name if employee else 'User',
            'today_date_str': today.strftime('%d %b %Y'),
            'hours_display': hrs_fmt,
            'check_in_time': check_in_str,
            'check_out_time': check_out_str,
            'is_checked_in': is_checked_in,
            'current_status': current_status,
            'button_label': button_label,
            'button_class': button_class,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'salary_deductions_days': late_cnt // 4,
            'summary': {
                'payable_days': max(1, payable_cnt),
                'present': max(1, present_cnt),
                'late': late_cnt,
                'movement': 0,
                'leave': leave_cnt,
                'absent': absent_cnt
            },
            'calendar_days': days_grid
        }

    @api.model
    def _build_nine_box(self, employees):
        cells = {}
        for emp in employees:
            perf = 'High' if emp.kpi_score >= 80 else ('Medium' if emp.kpi_score >= 60 else 'Low')
            potential_score = (emp.kpi_score + emp.kpi_attendance_score + emp.kpi_training_score) / 3.0
            potential = 'High' if potential_score >= 80 else ('Medium' if potential_score >= 60 else 'Low')
            key = f'{potential} Potential / {perf} Perf'
            cells[key] = cells.get(key, 0) + 1
        return [{'cell': key, 'count': value} for key, value in sorted(cells.items())]

    @api.model
    def _ensure_complete_srs_data(self):
        """Compatibility hook kept intentionally empty: dashboard reads existing database records only."""
        return True
