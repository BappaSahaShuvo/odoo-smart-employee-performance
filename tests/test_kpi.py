# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestKPI(TransactionCase):
    def setUp(self):
        super(TestKPI, self).setUp()
        self.emp = self.env['hr.employee'].create({'name': 'Grace Hopper'})

    def test_kpi_formula(self):
        kpi = self.env['employee.kpi'].create({
            'employee_id': self.emp.id,
            'task_completion': 100.0,
            'attendance_score': 100.0,
            'training_score': 100.0,
            'feedback_score': 100.0,
            'innovation_score': 100.0,
            'warning_deduction': 15.0
        })
        self.assertEqual(kpi.kpi_score, 85.0)