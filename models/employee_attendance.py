# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date, timedelta
import calendar

class EmployeeAttendanceLog(models.Model):
    _name = 'employee.attendance.log'
    _description = 'Employee Daily Attendance Record & Punctuality Policy'
    _order = 'date desc, check_in desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    check_in = fields.Datetime(string='Check In Time')
    check_out = fields.Datetime(string='Check Out Time')
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=False)

    expected_check_in_hour = fields.Float(string='Shift Start Hour', default=9.0)
    grace_period_minutes = fields.Integer(string='Grace Period (Mins)', default=10)
    is_late = fields.Boolean(string='Late Check-In', compute='_compute_punctuality', store=True)
    late_minutes = fields.Integer(string='Minutes Late', compute='_compute_punctuality', store=True)

    status = fields.Selection([
        ('present', 'Present (On Time)'),
        ('late', 'Late'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
        ('movement', 'Movement'),
        ('weekend', 'Weekend')
    ], string='Status', compute='_compute_status', store=True, readonly=False)

    salary_cut_day = fields.Float(string='Salary Deduction (Days)', compute='_compute_salary_deduction', store=True)

    @api.depends('check_in', 'expected_check_in_hour', 'grace_period_minutes')
    def _compute_punctuality(self):
        for rec in self:
            if rec.check_in:
                check_in_dt = fields.Datetime.to_datetime(rec.check_in)
                dt = fields.Datetime.context_timestamp(rec, check_in_dt)
                check_in_dec = dt.hour + (dt.minute / 60.0)
                allowed_cutoff = (rec.expected_check_in_hour or 9.0) + ((rec.grace_period_minutes or 10) / 60.0)

                if check_in_dec > allowed_cutoff:
                    rec.is_late = True
                    rec.late_minutes = max(0, int(round((check_in_dec - (rec.expected_check_in_hour or 9.0)) * 60)))
                else:
                    rec.is_late = False
                    rec.late_minutes = 0
            else:
                rec.is_late = False
                rec.late_minutes = 0

    @api.depends('check_in', 'is_late')
    def _compute_status(self):
        for rec in self:
            if rec.check_in:
                rec.status = 'late' if rec.is_late else 'present'
            elif not rec.status:
                rec.status = 'absent'

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                diff = fields.Datetime.to_datetime(rec.check_out) - fields.Datetime.to_datetime(rec.check_in)
                rec.worked_hours = round(diff.total_seconds() / 3600.0, 2)
            elif not rec.worked_hours:
                rec.worked_hours = 0.0

    @api.depends('employee_id', 'date', 'is_late')
    def _compute_salary_deduction(self):
        for rec in self:
            if not rec.employee_id or not rec.date:
                rec.salary_cut_day = 0.0
                continue
            rec_date = fields.Date.to_date(rec.date)
            month_start = date(rec_date.year, rec_date.month, 1)
            last_day = calendar.monthrange(rec_date.year, rec_date.month)[1]
            month_end = date(rec_date.year, rec_date.month, last_day)

            monthly_lates = self.env['employee.attendance.log'].sudo().search_count([
                ('employee_id', '=', rec.employee_id.id),
                ('date', '>=', month_start),
                ('date', '<=', month_end),
                ('is_late', '=', True)
            ])
            rec.salary_cut_day = round(monthly_lates / 4.0, 2)