# -*- coding: utf-8 -*-
from odoo import models, fields

class PromotionHistory(models.Model):
    _name = 'promotion.history'
    _description = 'Historical Promotion Log'
    _order = 'promotion_date desc, id desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    previous_job_id = fields.Many2one('hr.job', string='Previous Position', required=True)
    new_job_id = fields.Many2one('hr.job', string='Promoted Position', required=True)
    promotion_date = fields.Date(string='Promotion Date', default=fields.Date.context_today, required=True)
    notes = fields.Text(string='Promotion Notes')