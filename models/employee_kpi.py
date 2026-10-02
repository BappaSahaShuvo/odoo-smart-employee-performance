# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EmployeeKPI(models.Model):
    _name = 'employee.kpi'
    _description = 'Employee Monthly KPI Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    date = fields.Date(string='Evaluation Date', default=fields.Date.context_today, required=True)

    # 5 KPI Core Metrics[cite: 1]
    task_completion = fields.Float(string='Task Completion (30%)', default=80.0, tracking=True)
    attendance_score = fields.Float(string='Attendance (20%)', default=85.0, tracking=True)
    training_score = fields.Float(string='Training (20%)', default=80.0, tracking=True)
    feedback_score = fields.Float(string='Feedback (15%)', default=75.0, tracking=True)
    innovation_score = fields.Float(string='Innovation (15%)', default=70.0, tracking=True)

    warning_deduction = fields.Float(string='Warning Deduction', compute='_compute_warning_deduction', store=True)
    kpi_score = fields.Float(string='Calculated KPI Score', compute='_compute_kpi_score', store=True, tracking=True)

    kpi_category = fields.Selection([
        ('productivity', 'Productivity'),
        ('attendance', 'Attendance'),
        ('quality', 'Quality'),
        ('collaboration', 'Collaboration'),
        ('learning', 'Learning'),
        ('innovation', 'Innovation'),
        ('leadership', 'Leadership')
    ], default='productivity', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved')
    ], default='draft', tracking=True)

    @api.depends('employee_id', 'date')
    def _compute_warning_deduction(self):
        for rec in self:
            if not rec.employee_id or not rec.date:
                rec.warning_deduction = 0.0
                continue
            first_day = rec.date.replace(day=1)
            next_month = (first_day.replace(day=28) + fields.Date.to_date('2000-01-05').replace(day=5))
            last_day = next_month.replace(day=1) - fields.Date.to_date('2000-01-02').replace(day=1)

            warnings = self.env['warning.record'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'active'),
                ('date', '>=', first_day),
                ('date', '<=', last_day)
            ])
            rec.warning_deduction = sum(warnings.mapped('deduction_amount'))

    @api.depends('task_completion', 'attendance_score', 'training_score', 'feedback_score', 'innovation_score',
                 'warning_deduction')
    def _compute_kpi_score(self):
        for rec in self:
            raw_score = (
                    0.30 * rec.task_completion +
                    0.20 * rec.attendance_score +
                    0.20 * rec.training_score +
                    0.15 * rec.feedback_score +
                    0.15 * rec.innovation_score
            )
            final_score = raw_score - rec.warning_deduction
            rec.kpi_score = max(0.0, min(100.0, round(final_score, 2)))

    @api.constrains('task_completion', 'attendance_score', 'training_score', 'feedback_score', 'innovation_score')
    def _check_metric_limits(self):
        for rec in self:
            metrics = [rec.task_completion, rec.attendance_score, rec.training_score, rec.feedback_score,
                       rec.innovation_score]
            if any(m < 0.0 or m > 100.0 for m in metrics):
                raise ValidationError("All KPI component metrics must be scored between 0 and 100.")

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_approve(self):
        self.write({'state': 'approved'})
        for rec in self:
            rec.employee_id.kpi_score = rec.kpi_score
            rec.employee_id.kpi_attendance_score = rec.attendance_score
            rec.employee_id.kpi_training_score = rec.training_score