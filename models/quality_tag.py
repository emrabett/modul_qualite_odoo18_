# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class QualityTag(models.Model):
    _name = "quality.tag1"
    _description = "Quality Tag"

    name = fields.Char('Tag Name', required=True)
    color = fields.Integer('Color Index', help='Used in the kanban view')
