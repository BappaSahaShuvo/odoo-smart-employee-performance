# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WarningRecord(models.Model):
    _name = 'warning.record'
    _description = 'Disciplinary and Policy Warning'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    date = fields.Date(string='Date Issued', default=fields.Date.context_today, required=True)
    issued_by_id = fields.Many2one('res.users', string='Issued By', default=lambda self: self.env.user)

    warning_type = fields.Selection([
        ('attendance', 'Attendance Warning (-5 KPI)'),
        ('behavior', 'Behavior Warning (-10 KPI)'),
        ('performance', 'Performance Warning (-15 KPI)'),
        ('policy', 'Policy Violation (Blocks Promotion)')
    ], string='Warning Type', required=True, tracking=True)

    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium', required=True)

    deduction_amount = fields.Float(string='KPI Deduction', compute='_compute_effects', store=True)
    blocks_promotion = fields.Boolean(string='Blocks Promotion', compute='_compute_effects', store=True)
    reason = fields.Text(string='Reason & Notes', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('resolved', 'Resolved')
    ], default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('warning.record') or 'WARN'
        return super(WarningRecord, self).create(vals)

    @api.depends('warning_type')
    def _compute_effects(self):
        impact_map = {
            'attendance': (5.0, False),
            'behavior': (10.0, False),
            'performance': (15.0, False),
            'policy': (0.0, True),
        }
        for rec in self:
            deduction, block = impact_map.get(rec.warning_type, (0.0, False))
            rec.deduction_amount = deduction
            rec.blocks_promotion = block

    def action_activate(self):
        self.write({'state': 'active'})
        for rec in self:
            self.env['notification.service'].notify_warning_issued(rec)
            kpis = self.env['employee.kpi'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '!=', 'approved')
            ])
            kpis._compute_warning_deduction()
            kpis._compute_kpi_score()

    def action_resolve(self):
        self.write({'state': 'resolved'})