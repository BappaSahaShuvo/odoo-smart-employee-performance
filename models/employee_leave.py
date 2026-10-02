# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class EmployeeLeave(models.Model):
    _name = 'employee.leave'
    _description = 'Employee Leave Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    LEAVE_LIMITS = {
        'casual': 12,
        'sick': 14,
        'yearly': 10,
        'unpaid': 170,
    }

    name = fields.Char(string='Reference', readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self.env.user.employee_id.id or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id,
        tracking=True
    )
    employee_role = fields.Selection(
        related='employee_id.performance_role',
        string='Applicant Role',
        store=True
    )
    leave_type = fields.Selection([
        ('casual', 'Casual Leave (12 Days/Year)'),
        ('sick', 'Sick Leave (14 Days/Year)'),
        ('yearly', 'Yearly Leave (10 Days/Year)'),
        ('unpaid', 'Leave Without Pay (170 Days/Year)')
    ], string='Leave Category', required=True, default='casual', tracking=True)
    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    duration_days = fields.Integer(string='Duration (Days)', compute='_compute_duration', store=True, readonly=False)
    reason = fields.Text(string='Reason for Leave', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    approver_id = fields.Many2one('res.users', string='Reviewed By', readonly=True)
    approval_date = fields.Datetime(string='Decision Date', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                seq = self.env['ir.sequence'].next_by_code('employee.leave.seq')
                vals['name'] = seq or _('LV-%04d') % (self.search_count([]) + 1)
        return super(EmployeeLeave, self).create(vals_list)

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                d_from = fields.Date.to_date(rec.date_from)
                d_to = fields.Date.to_date(rec.date_to)

                if d_to < d_from:
                    rec.duration_days = 0
                else:
                    rec.duration_days = (d_to - d_from).days + 1
            else:
                rec.duration_days = 0

    def action_submit(self):
        for rec in self:
            rec._check_leave_allowance()
            rec.write({'state': 'submitted'})

    def _check_leave_allowance(self):
        today = fields.Date.context_today(self)
        year_start = date(today.year, 1, 1)
        year_end = date(today.year, 12, 31)
        allocated = self.LEAVE_LIMITS.get(self.leave_type, 0)
        taken_domain = [
            ('employee_id', '=', self.employee_id.id),
            ('leave_type', '=', self.leave_type),
            ('state', '=', 'approved'),
            ('date_from', '>=', year_start),
            ('date_to', '<=', year_end),
            ('id', '!=', self.id or 0)
        ]
        taken_days = sum(self.search(taken_domain).mapped('duration_days'))
        if (taken_days + (self.duration_days or 1)) > allocated:
            category_label = dict(self._fields['leave_type'].selection).get(self.leave_type, self.leave_type)
            raise ValidationError(_(
                "Leave limit exceeded for %s! Max: %d days, Approved: %d days, Requested: %d days."
            ) % (category_label, allocated, taken_days, self.duration_days or 1))

    def action_approve(self):
        for rec in self:
            rec.write({
                'state': 'approved',
                'approver_id': self.env.uid,
                'approval_date': fields.Datetime.now()
            })

    def action_reject(self):
        for rec in self:
            rec.write({
                'state': 'rejected',
                'approver_id': self.env.uid,
                'approval_date': fields.Datetime.now()
            })