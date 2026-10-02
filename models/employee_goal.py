# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EmployeeGoal(models.Model):
    _name = 'employee.goal'
    _description = 'Employee Goal Lifecycle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date asc, id desc'

    name = fields.Char(string='Goal Title', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    weightage = fields.Float(string='Weightage (%)', default=20.0, tracking=True)
    due_date = fields.Date(string='Due Date', required=True, tracking=True)
    progress = fields.Float(string='Progress (%)', default=0.0, tracking=True)
    comments = fields.Text(string='Manager / Approver Comments', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted to TL'),
        ('leader_approved', 'TL Approved'),
        ('manager_approved', 'Active'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ], default='draft', string='Status', tracking=True)

    @api.constrains('weightage', 'progress')
    def _check_ranges(self):
        for rec in self:
            if rec.weightage < 0.0 or rec.weightage > 100.0:
                raise ValidationError("Goal weightage must be between 0% and 100%.")
            if rec.progress < 0.0 or rec.progress > 100.0:
                raise ValidationError("Progress must be between 0% and 100%.")

    def action_submit(self):
        self.write({'state': 'submitted'})
        self.env['notification.service'].notify_goal_event(self, 'submitted')

    def action_tl_approve(self):
        self.write({'state': 'leader_approved'})
        self.env['notification.service'].notify_goal_event(self, 'leader_approved')

    def action_manager_approve(self):
        self.write({'state': 'manager_approved'})
        self.env['notification.service'].notify_goal_event(self, 'manager_approved')

    def action_complete(self):
        self.write({'state': 'completed', 'progress': 100.0})

    def action_reject(self):
        self.write({'state': 'rejected'})