# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv.expression import OR


class QualityAlertStage(models.Model):
    _name = "quality.alert.stage1"
    _description = "Quality Alert Stage"
    _order = "sequence, id"
    _fold_name = 'folded'

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence')
    folded = fields.Boolean('Folded')
    done = fields.Boolean('Alert Processed')
    team_ids = fields.Many2many('quality.team1', 'quality_alert_stage1_team_rel', 'stage_id', 'team_id', string='Teams')
