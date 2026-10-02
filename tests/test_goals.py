# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestGoals(TransactionCase):
    def setUp(self):
        super(TestGoals, self).setUp()
        self.emp = self.env['hr.employee'].create({'name': 'John von Neumann'})

    def test_goal_lifecycle(self):
        goal = self.env['employee.goal'].create({'name': 'Complete Architecture', 'employee_id': self.emp.id})
        self.assertEqual(goal.state, 'draft')
        goal.action_submit()
        self.assertEqual(goal.state, 'submitted')
        goal.action_tl_approve()
        self.assertEqual(goal.state, 'leader_approved')
        goal.action_manager_approve()
        self.assertEqual(goal.state, 'manager_approved')
        goal.action_complete()
        self.assertEqual(goal.state, 'completed')