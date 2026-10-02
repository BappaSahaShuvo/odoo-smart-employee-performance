# -*- coding: utf-8 -*-
from odoo import models, fields

class SkillMatrix(models.Model):
    _name = 'skill.matrix'
    _description = 'Employee Skill Proficiency Matrix'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    skill_category = fields.Selection([
        ('technical', 'Technical'),
        ('soft_skills', 'Soft Skills')
    ], default='technical', required=True)
    skill_name = fields.Char(string='Skill (e.g., Python, OWL, Leadership)', required=True)
    proficiency_level = fields.Selection([
        ('1', '1 - Novice'),
        ('2', '2 - Basic'),
        ('3', '3 - Competent'),
        ('4', '4 - Proficient'),
        ('5', '5 - Expert')
    ], default='3', required=True)
    target_level = fields.Selection([
        ('1', '1 - Novice'),
        ('2', '2 - Basic'),
        ('3', '3 - Competent'),
        ('4', '4 - Proficient'),
        ('5', '5 - Expert')
    ], default='4', required=True)