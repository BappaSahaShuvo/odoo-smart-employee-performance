# -*- coding: utf-8 -*-
from odoo import models, fields


class PerformanceReview(models.Model):
    _name = 'performance.review'
    _description = 'Multi-Level Performance Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    review_period = fields.Char(string='Review Period (e.g. 2026-Q1)', required=True)

    self_rating = fields.Float(string='Self Rating (0-5)', default=4.0)
    self_comments = fields.Text(string='Self Review Comments')

    tl_rating = fields.Float(string='Team Leader Rating (0-5)', default=4.0)
    tl_comments = fields.Text(string='Team Leader Feedback')

    manager_rating = fields.Float(string='Manager Rating (0-5)', default=4.0)
    manager_comments = fields.Text(string='Manager Feedback')

    hr_rating = fields.Float(string='HR Rating (0-5)', default=4.0)
    hr_comments = fields.Text(string='HR Observations')

    overall_score = fields.Float(string='Consolidated Score (%)', default=80.0)
    state = fields.Selection([
        ('draft', 'Self Review'),
        ('tl_review', 'Team Leader Review'),
        ('manager_review', 'Manager Review'),
        ('hr_review', 'HR Review'),
        ('completed', 'Completed')
    ], default='draft', tracking=True)

    def action_submit_tl(self): self.write({'state': 'tl_review'})

    def action_submit_mgr(self): self.write({'state': 'manager_review'})

    def action_submit_hr(self): self.write({'state': 'hr_review'})

    def action_complete(self): self.write({'state': 'completed'})