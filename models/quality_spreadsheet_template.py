# -*- coding: utf-8 -*-

from odoo import fields, models


class QualitySpreadsheetTemplate(models.Model):
    _name = 'quality.spreadsheet.template1'
    _description = "Quality check template spreadsheet"

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.company
    )
    check_cell = fields.Char(
        string="Success cell",
        default='A1',
        help="The check is successful if the success cell value is TRUE. If there are"
        " several sheets, specify which one you want to use (e.g. Sheet2!C4). If not "
        "specified, the first sheet is selected by default.",
    )
    spreadsheet_file_name = fields.Char('File Name')
    spreadsheet_binary_data = fields.Binary('Spreadsheet Data')

    def action_open_spreadsheet(self):
        """Action to open spreadsheet editor"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Spreadsheet',
            'res_model': 'quality.spreadsheet.template1',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
