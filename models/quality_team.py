# -*- coding: utf-8 -*-

import ast

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv.expression import OR


class QualityTeam1(models.Model):
    _name = "quality.team1"
    _description = "Quality Alert Team"
    _inherit = ['mail.alias.mixin', 'mail.thread']
    _order = "sequence, id"

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', index=True)
    sequence = fields.Integer('Sequence')
    check_count = fields.Integer('# Quality Checks', compute='_compute_check_count')
    alert_count = fields.Integer('# Quality Alerts', compute='_compute_alert_count')
    color = fields.Integer('Color', default=1)

    def _compute_check_count(self):
        check_data = self.env['quality.check1']._read_group([('team_id1', 'in', self.ids), ('quality_state', '=', 'none')], ['team_id1'], ['__count'])
        check_result = {team.id: count for team, count in check_data}
        for team in self:
            team.check_count = check_result.get(team.id, 0)

    def _compute_alert_count(self):
        alert_data = self.env['quality.alert1']._read_group([('team_id1', 'in', self.ids), ('stage_id1.done', '=', False)], ['team_id1'], ['__count'])
        alert_result = {team.id: count for team, count in alert_data}
        for team in self:
            team.alert_count = alert_result.get(team.id, 0)

    @api.model
    def _get_quality_team(self, domain):
        team_id = self.env['quality.team1'].search(domain, limit=1).id
        if team_id:
            return team_id
        else:
            raise UserError(_("No quality team found for this company.\n"
                              "Please go to configuration and create one first."))

    def _alias_get_creation_values(self):
        values = super(QualityTeam1, self)._alias_get_creation_values()
        values['alias_model_id'] = self.env['ir.model']._get('quality.alert1').id
        if self.id:
            values['alias_defaults'] = defaults = ast.literal_eval(self.alias_defaults or "{}")
            defaults['team_id1'] = self.id
            defaults['company_id'] = self.company_id.id
        return values