# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestPromotion(TransactionCase):
    def setUp(self):
        super(TestPromotion, self).setUp()
        self.emp = self.env['hr.employee'].create({'name': 'Claude Shannon', 'kpi_score': 60.0})
        self.job1 = self.env['hr.job'].create({'name': 'Engineer'})
        self.job2 = self.env['hr.job'].create({'name': 'Lead'})

    def test_promotion_eligibility_block(self):
        promo = self.env['promotion.request'].create({
            'employee_id': self.emp.id,
            'current_job_id': self.job1.id,
            'recommended_job_id': self.job2.id
        })
        with self.assertRaises(UserError):
            promo.action_submit_tl()