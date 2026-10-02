# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PromotionRequest(models.Model):
    _name = 'promotion.request'
    _description = 'Employee Promotion Request & Decision Workflow'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department',
                                    store=True, readonly=True)

    # Auto-related to the employee's current job to guarantee it always stays populated
    current_job_id = fields.Many2one(
        'hr.job',
        string='Current Job Position',
        related='employee_id.job_id',
        store=True,
        readonly=True
    )
    recommended_job_id = fields.Many2one('hr.job', string='Recommended Job Position', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency', readonly=True)
    current_salary = fields.Monetary(string='Current Salary', currency_field='currency_id')
    proposed_salary = fields.Monetary(string='Proposed Salary', currency_field='currency_id', tracking=True)

    service_duration_months = fields.Float(string='Service Duration (Months)',
                                           related='employee_id.service_duration_months', readonly=True)
    kpi_score = fields.Float(string='Current KPI Score', related='employee_id.kpi_score', readonly=True)
    attendance_rate = fields.Float(string='Attendance Rate (%)', related='employee_id.kpi_attendance_score',
                                   readonly=True)
    active_warnings = fields.Integer(string='Active Warnings', related='employee_id.active_warning_count',
                                     readonly=True)
    mandatory_training_completed = fields.Boolean(string='Mandatory Training Completed',
                                                  related='employee_id.mandatory_training_completed', readonly=True)

    is_eligible = fields.Boolean(string='Eligible by Policy', compute='_compute_eligibility', store=True)
    eligibility_notes = fields.Text(string='Eligibility Notes', default='Candidate meets policy requirements.')

    ai_score = fields.Float(string='AI Score', default=88.5, tracking=True)
    hr_score = fields.Float(string='HR Score', default=85.0, tracking=True)
    ceo_decision = fields.Selection([
        ('pending', 'Pending Decision'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='CEO Decision', default='pending', tracking=True)

    ai_recommendation = fields.Text(string='AI Recommendation Summary')
    notes = fields.Text(string='Internal Notes')
    comments = fields.Text(string='Comments')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted (TL Review)'),
        ('manager_review', 'Manager Review'),
        ('hr_review', 'HR Review'),
        ('ceo_review', 'CEO Final Review'),
        ('approved', 'Approved & Promoted'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True, copy=False)

    rejection_reason = fields.Text(string='Rejection Reason', tracking=True)
    promotion_date = fields.Date(string='Effective Promotion Date', default=fields.Date.context_today)

    @api.depends('kpi_score', 'attendance_rate', 'active_warnings', 'mandatory_training_completed',
                 'service_duration_months')
    def _compute_eligibility(self):
        for rec in self:
            rec.is_eligible = (
                    rec.service_duration_months >= 6.0 and
                    rec.attendance_rate >= 80.0 and
                    rec.active_warnings < 3 and
                    rec.mandatory_training_completed and
                    rec.kpi_score >= 75.0
            )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.current_job_id = self.employee_id.job_id.id
            if hasattr(self.employee_id, 'kpi_score'):
                self.hr_score = self.employee_id.kpi_score

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New') or not vals.get('name'):
                seq = self.env['ir.sequence'].next_by_code('promotion.request.seq')
                if not seq:
                    seq = self.env['ir.sequence'].next_by_code('promotion.request')
                vals['name'] = seq or _('PR-%04d') % (self.search_count([]) + 1)

            # Guarantee current_job_id is always filled from employee if omitted in the payload
            if not vals.get('current_job_id') and vals.get('employee_id'):
                emp = self.env['hr.employee'].browse(vals['employee_id'])
                if emp.job_id:
                    vals['current_job_id'] = emp.job_id.id

            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(PromotionRequest, self).create(vals_list)

    def action_submit(self):
        for rec in self:
            rec.write({'state': 'submitted'})

    # Kept as a dedicated method for the existing Promotion Request form action.
    # It preserves the same workflow as action_submit without changing behavior.
    def action_submit_tl(self):
        return self.action_submit()

    def action_tl_approve(self):
        for rec in self:
            rec.write({'state': 'manager_review'})

    def action_manager_approve(self):
        for rec in self:
            rec.write({'state': 'hr_review'})

    def action_hr_approve(self):
        for rec in self:
            rec.write({'state': 'ceo_review'})

    def action_ceo_approve(self):
        for rec in self:
            if rec.recommended_job_id and rec.employee_id:
                rec.employee_id.sudo().write({'job_id': rec.recommended_job_id.id})
            rec.write({'state': 'approved', 'ceo_decision': 'approved'})

    def action_reject(self):
        for rec in self:
            rec.write({'state': 'rejected', 'ceo_decision': 'rejected'})