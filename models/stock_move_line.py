# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # Champs pour les contrôles qualité
    check_state1 = fields.Selection([
        ('none', 'Aucun'),
        ('in_progress', 'En Cours'),
        ('pass', 'Réussi'),
        ('fail', 'Échoué'),
    ], string="État du Contrôle", default='none')

    def action_open_quality_check_wizard1(self):
        """Ouvrir le wizard de contrôle qualité"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrôle Qualité',
            'res_model': 'quality.check.wizard1',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_line_id1': self.id,
            }
        }