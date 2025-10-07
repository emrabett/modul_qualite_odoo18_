# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class TestType(models.Model):
    _name = "quality.point.test_type1"
    _description = "Quality Control Test Type"

    # Used instead of selection field in order to hide a choice depending on the view.
    name = fields.Char('Name', required=True, translate=True)
    technical_name = fields.Char('Technical name', required=True)
    active = fields.Boolean('active', default=True)
