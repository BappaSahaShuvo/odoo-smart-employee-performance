# -*- coding: utf-8 -*-
from odoo import models, api

class NotificationService(models.AbstractModel):
    _name = 'notification.service'
    _description = 'System Notification Dispatcher'

    @api.model
    def notify_goal_event(self, goal, event_type):
        pass

    @api.model
    def notify_warning_issued(self, warning):
        warning.employee_id.message_post(body=f"Disciplinary Warning issued: {warning.warning_type}. Impact: -{warning.deduction_amount} KPI points.")

    @api.model
    def notify_promotion_status(self, promo, status):
        promo.employee_id.message_post(body=f"Promotion dossier update: {status}.")