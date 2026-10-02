# -*- coding: utf-8 -*-
from odoo import models, fields

class RewardRecord(models.Model):
    _name = 'reward.record'
    _description = 'Employee Recognition and Rewards'
    _inherit = ['mail.thread']

    name = fields.Char(string='Reward Title', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date = fields.Date(string='Date Awarded', default=fields.Date.context_today, required=True)
    reward_type = fields.Selection([
        ('employee_of_month', 'Employee of Month'),
        ('certificate', 'Certificate of Merit'),
        ('cash_bonus', 'Cash Bonus'),
        ('gift_voucher', 'Gift Voucher'),
        ('badge', 'Appreciation Badge')
    ], string='Reward Type', default='badge', required=True)
    points = fields.Integer(string='Reward Points', default=100)
    reason = fields.Text(string='Citation & Reason', required=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By', default=lambda self: self.env.user)