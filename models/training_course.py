# -*- coding: utf-8 -*-
from odoo import models, fields

class TrainingCourse(models.Model):
    _name = 'training.course'
    _description = 'Training Catalog Course'

    name = fields.Char(string='Course Title', required=True)
    category = fields.Selection([
        ('technical', 'Technical Development'),
        ('soft_skills', 'Soft Skills & Leadership'),
        ('compliance', 'Compliance & Safety')
    ], default='technical', required=True)
    duration_hours = fields.Float(string='Duration (Hours)', default=8.0)
    is_mandatory = fields.Boolean(string='Mandatory for Promotion', default=False)
    description = fields.Text(string='Course Syllabus')