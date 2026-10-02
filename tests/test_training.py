# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestTraining(TransactionCase):
    def setUp(self):
        super(TestTraining, self).setUp()
        self.emp = self.env['hr.employee'].create({'name': 'Margaret Hamilton'})
        self.course = self.env['training.course'].create({'name': 'OWL Advanced', 'is_mandatory': True})

    def test_enrollment_completion(self):
        enroll = self.env['training.enrollment'].create({'employee_id': self.emp.id, 'course_id': self.course.id})
        self.assertEqual(enroll.state, 'assigned')
        enroll.action_complete()
        self.assertEqual(enroll.state, 'completed')
        self.assertTrue(self.emp.mandatory_training_completed)