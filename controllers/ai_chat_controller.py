# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class AIChatController(http.Controller):

    @http.route('/smart_performance/ai_chat', type='json', auth='user')
    def process_ai_chat_message(self, prompt=None, query=None, employee_id=None):
        prompt = prompt or query
        if not prompt:
            return {'reply': "How may I assist you with performance evaluation, attendance policies, or promotion criteria today?"}

        # Query dynamic Ollama AI service
        reply_text = request.env['ai.service'].generate_dynamic_ai_response(
            user_prompt=prompt,
            target_employee_id=employee_id
        )
        return {'reply': reply_text, 'response': reply_text}