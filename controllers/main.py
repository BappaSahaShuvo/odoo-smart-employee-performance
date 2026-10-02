# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import csv
import io
import logging

_logger = logging.getLogger(__name__)

class SmartPerformanceController(http.Controller):

    @http.route('/smart_performance/login', type='json', auth='public', methods=['POST'])
    def dashboard_login(self, login=None, password=None):
        return request.env['dashboard.service'].authenticate_dashboard_user(login, password)

    @http.route('/smart_performance/dashboard_data', type='json', auth='user', methods=['POST'])
    def get_dashboard_data(self, dashboard_type='ceo', filters=None, active_role=None, target_employee_id=None):
        return request.env['dashboard.service'].get_dashboard_data(
            dashboard_type=dashboard_type,
            filters=filters,
            active_role=active_role,
            target_employee_id=target_employee_id
        )

    @http.route('/smart_performance/attendance_punch', type='json', auth='user', methods=['POST'])
    def attendance_punch(self, employee_id=None):
        return request.env['dashboard.service'].execute_punch_action(employee_id=employee_id)

    @http.route('/smart_performance/submit_leave', type='json', auth='user', methods=['POST'])
    def submit_leave(self, vals=None):
        return request.env['dashboard.service'].submit_leave_request(vals or {})

    @http.route('/smart_performance/process_leave_decision', type='json', auth='user', methods=['POST'])
    def process_leave_decision(self, leave_id=None, decision=None, current_role='admin'):
        return request.env['dashboard.service'].process_leave_decision(
            leave_id=leave_id,
            decision=decision,
            current_role=current_role
        )
    @http.route('/smart_performance/export_kpi_xlsx', type='http', auth='user', methods=['GET'])
    def export_kpi_xlsx(self, employee_id=None, **kwargs):
        """Download the live KPI report as an XLSX file instead of redirecting to a missing route."""
        try:
            import xlsxwriter
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet('KPI Summary')
            header = workbook.add_format({'bold': True, 'bg_color': '#4F46E5', 'font_color': '#FFFFFF', 'border': 1})
            cell = workbook.add_format({'border': 1})
            num = workbook.add_format({'border': 1, 'num_format': '0.00'})
            headers = ['Employee', 'Department', 'Date', 'KPI Category', 'Task Completion (30%)', 'Attendance (20%)', 'Training (20%)', 'Feedback (15%)', 'Innovation (15%)', 'Deductions', 'Final KPI', 'Status']
            for col, title in enumerate(headers):
                sheet.write(0, col, title, header)
                sheet.set_column(col, col, 20)
            domain = []
            try:
                employee_id = int(employee_id) if employee_id else None
            except (TypeError, ValueError):
                employee_id = None
            if request.env.user.has_group('smart_employee_performance_management.group_performance_employee') and employee_id:
                domain.append(('employee_id', '=', employee_id))
            elif employee_id:
                domain.append(('employee_id', '=', employee_id))
            records = request.env['employee.kpi'].sudo().search(domain, order='date desc')
            for row, rec in enumerate(records, start=1):
                values = [rec.employee_id.name or '', rec.department_id.name or '', str(rec.date or ''), dict(rec._fields['kpi_category'].selection).get(rec.kpi_category, ''), rec.task_completion, rec.attendance_score, rec.training_score, rec.feedback_score, rec.innovation_score, rec.warning_deduction, rec.kpi_score, rec.state.capitalize() if rec.state else '']
                for col, value in enumerate(values):
                    sheet.write(row, col, value, num if isinstance(value, (int, float)) else cell)
            workbook.close()
            output.seek(0)
            return request.make_response(output.getvalue(), headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'), ('Content-Disposition', 'attachment; filename="kpi_performance_report.xlsx"')])
        except Exception:
            _logger.exception('KPI XLSX export failed')
            return request.not_found()

    @http.route('/smart_performance/export_kpi_csv', type='http', auth='user', methods=['GET'])
    def export_kpi_csv(self, employee_id=None, **kwargs):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Employee', 'Department', 'Date', 'KPI Category', 'Task Completion (30%)', 'Attendance (20%)', 'Training (20%)', 'Feedback (15%)', 'Innovation (15%)', 'Deductions', 'Final KPI', 'Status'])
        try:
            employee_id = int(employee_id) if employee_id else None
        except (TypeError, ValueError):
            employee_id = None
        domain = [('employee_id', '=', employee_id)] if employee_id else []
        records = request.env['employee.kpi'].sudo().search(domain, order='date desc')
        for rec in records:
            writer.writerow([rec.employee_id.name or '', rec.department_id.name or '', str(rec.date or ''), dict(rec._fields['kpi_category'].selection).get(rec.kpi_category, ''), rec.task_completion, rec.attendance_score, rec.training_score, rec.feedback_score, rec.innovation_score, rec.warning_deduction, rec.kpi_score, rec.state.capitalize() if rec.state else ''])
        return request.make_response(output.getvalue().encode('utf-8-sig'), headers=[('Content-Type', 'text/csv; charset=utf-8'), ('Content-Disposition', 'attachment; filename="kpi_performance_report.csv"')])
