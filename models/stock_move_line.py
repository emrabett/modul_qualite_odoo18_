# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # Champs pour les contrôles qualité personnalisés
    check_ids1 = fields.One2many('quality.check1', 'move_line_id1', 'Contrôles Qualité')
    check_state1 = fields.Selection([
        ('no_checks', 'Aucun contrôle'),
        ('in_progress', 'En cours'),
        ('pass', 'Réussi'),
        ('fail', 'Échoué')
    ], string="État du Contrôle", compute="_compute_check_state1", store=True)

    @api.depends('check_ids1', 'check_ids1.quality_state')
    def _compute_check_state1(self):
        """Calculer l'état du contrôle qualité basé sur les checks"""
        for line in self:
            if not line.check_ids1:
                line.check_state1 = 'no_checks'
            elif line.check_ids1.filtered(lambda check: check.quality_state == 'none'):
                line.check_state1 = 'in_progress'
            elif line.check_ids1.filtered(lambda check: check.quality_state == 'fail'):
                line.check_state1 = 'fail'
            else:
                line.check_state1 = 'pass'

    def action_open_quality_check_wizard1(self):
        """Ouvrir le wizard de contrôle qualité - Identique à la version entreprise"""
        return self.check_ids1.action_open_quality_check_wizard1()