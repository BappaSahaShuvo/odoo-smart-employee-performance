# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestAI(TransactionCase):
    def test_ai_fallback(self):
        res = self.env['ai.service']._call_llm("sys", "user query")
        self.assertTrue(len(res) > 0)