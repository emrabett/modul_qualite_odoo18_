# -*- coding: utf-8 -*-

from odoo import api, fields, models


class QualityCheckSpreadsheet(models.Model):
    _name = 'quality.check.spreadsheet1'
    _description = "Quality check spreadsheet"

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company
    )
    check_cell = fields.Char(
        string="Success cell",
        help="The check is successful if the success cell value is TRUE. If there are"
        " several sheets, specify which one you want to use (e.g. Sheet2!C4). If not "
        "specified, the first sheet is selected by default.",
    )
    spreadsheet_file_name = fields.Char('File Name')
    spreadsheet_binary_data = fields.Binary('Spreadsheet Data')
    quality_check_id = fields.Many2one('quality.check1', 'Quality Check')

    def action_open_spreadsheet(self):
        """Action to open spreadsheet editor"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Spreadsheet',
            'res_model': 'quality.check.spreadsheet1',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.autovacuum
    def _gc_spreadsheet_history(self):
        """Clean up old spreadsheet history"""
        # Placeholder for spreadsheet history cleanup
        pass
