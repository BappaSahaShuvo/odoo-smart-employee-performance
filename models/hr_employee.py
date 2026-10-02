# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Roles and Shifts
    performance_role = fields.Selection([
        ('admin', 'System Administrator'),
        ('ceo', 'Chief Executive Officer (CEO)'),
        ('hr', 'Human Resources (HR)'),
        ('manager', 'Department Manager'),
        ('team_leader', 'Team Leader'),
        ('employee', 'Standard Employee')
    ], string='System Role', default='employee', required=True)

    shift_type = fields.Selection([
        ('morning', 'Morning Shift (08:00 AM - 04:00 PM)'),
        ('evening', 'Evening Shift (04:00 PM - 12:00 AM)'),
        ('night', 'Night Shift (12:00 AM - 08:00 AM)'),
        ('general', 'General Office (09:00 AM - 05:00 PM)')
    ], string='Assigned Shift', default='general')

    # Profile Header Fields
    employee_code = fields.Char(string='Employee ID')
    personal_phone = fields.Char(string='Personal Number')
    official_phone = fields.Char(string='Official Number')
    employment_status = fields.Char(string='Employment Status')
    joining_date = fields.Date(string='Joining Date')
    service_length_str = fields.Char(string='Service Length', compute='_compute_service_length_str')

    supervisor_name = fields.Char(string='Supervisor')
    dotted_supervisor_name = fields.Char(string='Dotted Supervisor')
    line_manager_name = fields.Char(string='Line Manager')

    # Performance & Promotion Fields (Required by views/hr_employee_views.xml)
    kpi_score = fields.Float(string='Current KPI Score', default=75.0, tracking=True)
    kpi_attendance_score = fields.Float(string='Attendance %', default=90.0, tracking=True)
    kpi_training_score = fields.Float(string='Training Completion %', default=85.0, tracking=True)
    service_duration_months = fields.Float(string='Service Duration (Months)', compute='_compute_service_duration')

    active_warning_count = fields.Integer(string='Active Warnings Count', compute='_compute_warning_status', store=True)
    has_policy_violation = fields.Boolean(string='Has Active Policy Violation', compute='_compute_warning_status', store=True)
    mandatory_training_completed = fields.Boolean(string='Mandatory Training Done', compute='_compute_training_status', store=True)

    attrition_risk_score = fields.Float(string='Attrition Risk Score (%)', default=15.0)
    promotion_probability = fields.Float(string='Promotion Probability (%)', default=65.0)

    # Relational mappings
    goal_ids = fields.One2many('employee.goal', 'employee_id', string='Goals')
    kpi_ids = fields.One2many('employee.kpi', 'employee_id', string='KPI Records')
    warning_ids = fields.One2many('warning.record', 'employee_id', string='Disciplinary Warnings')
    reward_ids = fields.One2many('reward.record', 'employee_id', string='Awards & Rewards')
    training_enrollment_ids = fields.One2many('training.enrollment', 'employee_id', string='Course Enrollments')
    skill_matrix_ids = fields.One2many('skill.matrix', 'employee_id', string='Skill Matrix')
    career_path_id = fields.Many2one('career.path', string='Career Path Roadmap')
    leave_ids = fields.One2many('employee.leave', 'employee_id', string='Leave Applications')

    # Dynamic metrics
    current_kpi_score = fields.Float(string='Dynamic KPI Score', compute='_compute_employee_stats')
    attendance_rate = fields.Float(string='Attendance Rate (%)', compute='_compute_employee_stats')
    missed_days_count = fields.Integer(string='Recent Unexcused Missed Days', compute='_compute_attendance_penalties')
    ai_attendance_notice = fields.Char(string='AI Warning Notice', compute='_compute_attendance_penalties')

    casual_leave_remaining = fields.Integer(string='Casual Leave Remaining', compute='_compute_leave_balances')
    sick_leave_remaining = fields.Integer(string='Sick Leave Remaining', compute='_compute_leave_balances')
    yearly_leave_remaining = fields.Integer(string='Yearly Leave Remaining', compute='_compute_leave_balances')
    unpaid_leave_remaining = fields.Integer(string='Unpaid Leave Remaining', compute='_compute_leave_balances')

    @api.depends('joining_date')
    def _compute_service_length_str(self):
        today = fields.Date.today()
        for rec in self:
            j_date = rec.joining_date or today
            total_days = (today - j_date).days
            if total_days <= 0:
                rec.service_length_str = "0 years 0 months 0 days"
                continue
            years = total_days // 365
            rem_days = total_days % 365
            months = rem_days // 30
            days = rem_days % 30
            rec.service_length_str = f"{years} years {months} months {days} days"

    @api.depends('joining_date')
    def _compute_service_duration(self):
        today = fields.Date.today()
        for rec in self:
            start_date = rec.joining_date or today
            delta_days = (today - start_date).days
            rec.service_duration_months = round(delta_days / 30.0, 1)

    @api.depends('warning_ids.state', 'warning_ids.warning_type')
    def _compute_warning_status(self):
        for rec in self:
            active_warnings = rec.warning_ids.filtered(lambda w: w.state == 'active')
            rec.active_warning_count = len(active_warnings)
            rec.has_policy_violation = any(w.warning_type == 'policy' for w in active_warnings)

    @api.depends('training_enrollment_ids.state', 'training_enrollment_ids.course_id.is_mandatory')
    def _compute_training_status(self):
        for rec in self:
            mandatory_enrollments = rec.training_enrollment_ids.filtered(lambda e: e.course_id.is_mandatory)
            if not mandatory_enrollments:
                rec.mandatory_training_completed = True
            else:
                rec.mandatory_training_completed = all(e.state == 'completed' for e in mandatory_enrollments)

    def _compute_employee_stats(self):
        for emp in self:
            latest_kpi = self.env['employee.kpi'].search([('employee_id', '=', emp.id)], order='create_date desc', limit=1)
            emp.current_kpi_score = latest_kpi.kpi_score if latest_kpi else emp.kpi_score
            emp.attendance_rate = emp.kpi_attendance_score or 98.0

    def _compute_attendance_penalties(self):
        AttObj = self.env['employee.attendance.log']
        thirty_days_ago = fields.Date.today() - timedelta(days=30)
        for emp in self:
            absences = AttObj.search_count([
                ('employee_id', '=', emp.id),
                ('status', '=', 'absent'),
                ('date', '>=', thirty_days_ago)
            ])
            emp.missed_days_count = absences
            if absences >= 3:
                emp.ai_attendance_notice = (
                    "AI Automated Warning: You have missed 3 days without authorization. "
                    "If you miss another one day then you will lose one day salary."
                )
            else:
                emp.ai_attendance_notice = ""

    def _compute_leave_balances(self):
        year_start = date(fields.Date.today().year, 1, 1)
        year_end = date(fields.Date.today().year, 12, 31)
        Leave = self.env['employee.leave']
        for emp in self:
            leaves = Leave.search([
                ('employee_id', '=', emp.id),
                ('state', '=', 'approved'),
                ('date_from', '>=', year_start),
                ('date_to', '<=', year_end)
            ])
            c_used = sum(leaves.filtered(lambda l: l.leave_type == 'casual').mapped('duration_days'))
            s_used = sum(leaves.filtered(lambda l: l.leave_type == 'sick').mapped('duration_days'))
            y_used = sum(leaves.filtered(lambda l: l.leave_type == 'yearly').mapped('duration_days'))
            u_used = sum(leaves.filtered(lambda l: l.leave_type == 'unpaid').mapped('duration_days'))

            emp.casual_leave_remaining = max(0, 12 - c_used)
            emp.sick_leave_remaining = max(0, 14 - s_used)
            emp.yearly_leave_remaining = max(0, 10 - y_used)
            emp.unpaid_leave_remaining = max(0, 170 - u_used)

    def write(self, vals):
        if self.env.su:
            return super(HrEmployee, self).write(vals)

        is_hr_or_admin = self.env.user.has_group('smart_employee_performance_management.group_performance_hr') or self.env.user.has_group('base.group_system')
        allowed_shift_updaters = ('group_performance_team_leader', 'group_performance_manager', 'group_performance_ceo', 'group_performance_hr')
        has_shift_privilege = any(self.env.user.has_group(f'smart_employee_performance_management.{g}') for g in allowed_shift_updaters) or self.env.user.has_group('base.group_system')

        restricted_keys = set(vals.keys()) - {'shift_type', 'message_follower_ids', 'activity_ids', 'message_ids'}
        if restricted_keys and not is_hr_or_admin:
            raise UserError(_("Security Restriction: Master employee details can only be registered and modified by Human Resources (HR)."))
        if 'shift_type' in vals and not has_shift_privilege:
            raise UserError(_("You do not have permission to modify employee work shifts."))
        return super(HrEmployee, self).write(vals)