# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class QualityReason(models.Model):
    _name = "quality.reason1"
    _description = "Root Cause for Quality Failure"

    name = fields.Char('Name', required=True, translate=True)
