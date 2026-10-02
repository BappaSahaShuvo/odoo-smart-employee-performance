# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestWarning(TransactionCase):
    def setUp(self):
        super(TestWarning, self).setUp()
        self.emp = self.env['hr.employee'].create({'name': 'Nikola Tesla'})

    def test_warning_deductions(self):
        w_att = self.env['warning.record'].create({'employee_id': self.emp.id, 'warning_type': 'attendance', 'reason': 'Late'})
        self.assertEqual(w_att.deduction_amount, 5.0)
        w_pol = self.env['warning.record'].create({'employee_id': self.emp.id, 'warning_type': 'policy', 'reason': 'Violation'})
        self.assertTrue(w_pol.blocks_promotion)