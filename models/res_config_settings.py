# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_enabled = fields.Boolean(string='Enable AI Insights', config_parameter='smart_performance.ai_enabled', default=True)
    ai_provider = fields.Selection([
        ('openai', 'OpenAI API'),
        ('local_llm', 'Local LLM (Ollama / vLLM)')
    ], string='AI Provider', config_parameter='smart_performance.ai_provider', default='local_llm')
    ai_api_key = fields.Char(string='AI API Key', config_parameter='smart_performance.ai_api_key')
    ai_endpoint = fields.Char(string='AI Endpoint', config_parameter='smart_performance.ai_endpoint', default='http://127.0.0.1:11434/api/chat')
    ai_model = fields.Char(string='AI Model', config_parameter='smart_performance.ai_model', default='llama3.2')