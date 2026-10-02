# -*- coding: utf-8 -*-
import io
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.warning("xlsxwriter module not found in Python environment.")
    xlsxwriter = None


class ReportKPIXLSX(models.AbstractModel):
    _name = 'report.smart_employee_performance_management.kpi_xlsx'
    _description = 'Native KPI Spreadsheet Generator'

    @api.model
    def generate_kpi_xlsx(self, kpi_ids=None):
        if not xlsxwriter:
            return None

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('KPI Summary')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F46E5',
            'font_color': '#FFFFFF',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        num_format = workbook.add_format({'border': 1, 'num_format': '0.00', 'align': 'right'})

        headers = [
            'Employee', 'Department', 'Date', 'KPI Category',
            'Task Completion (30%)', 'Attendance (20%)', 'Training (20%)',
            'Feedback (15%)', 'Innovation (15%)', 'Deductions', 'Final KPI', 'Status'
        ]

        for col, title in enumerate(headers):
            sheet.write(0, col, title, header_format)
            sheet.set_column(col, col, 18)

        domain = [('id', 'in', kpi_ids)] if kpi_ids else []
        records = self.env['employee.kpi'].search(domain, order='date desc')

        for row, rec in enumerate(records, start=1):
            sheet.write(row, 0, rec.employee_id.name or '', cell_format)
            sheet.write(row, 1, rec.department_id.name or 'N/A', cell_format)
            sheet.write(row, 2, str(rec.date or ''), cell_format)
            sheet.write(row, 3, dict(rec._fields['kpi_category'].selection).get(rec.kpi_category, ''), cell_format)
            sheet.write(row, 4, rec.task_completion, num_format)
            sheet.write(row, 5, rec.attendance_score, num_format)
            sheet.write(row, 6, rec.training_score, num_format)
            sheet.write(row, 7, rec.feedback_score, num_format)
            sheet.write(row, 8, rec.innovation_score, num_format)
            sheet.write(row, 9, rec.warning_deduction, num_format)
            sheet.write(row, 10, rec.kpi_score, num_format)
            sheet.write(row, 11, rec.state.capitalize() if rec.state else '', cell_format)

        workbook.close()
        output.seek(0)
        return output.read()