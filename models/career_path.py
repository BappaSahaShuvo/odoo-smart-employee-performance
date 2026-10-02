# -*- coding: utf-8 -*-
from odoo import models, fields

class CareerPath(models.Model):
    _name = 'career.path'
    _description = 'Employee Career Progression Roadmap'

    name = fields.Char(string='Roadmap Title', required=True)
    current_job_id = fields.Many2one('hr.job', string='Starting Position', required=True)
    target_job_id = fields.Many2one('hr.job', string='Target Position', required=True)
    required_kpi_score = fields.Float(string='Minimum Required KPI', default=80.0)
    required_skills = fields.Text(string='Required Technical & Soft Competencies')
    recommended_training = fields.Text(string='Required Training Modules')