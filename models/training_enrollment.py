# -*- coding: utf-8 -*-
from odoo import models, fields

class TrainingEnrollment(models.Model):
    _name = 'training.enrollment'
    _description = 'Employee Training Enrollment'

    course_id = fields.Many2one('training.course', string='Course', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    progress_pct = fields.Float(string='Progress (%)', default=0.0)
    score = fields.Float(string='Assessment Score (%)', default=0.0)
    state = fields.Selection([
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], default='assigned')

    def action_start(self): self.write({'state': 'in_progress'})
    def action_complete(self): self.write({'state': 'completed', 'progress_pct': 100.0, 'score': 95.0})