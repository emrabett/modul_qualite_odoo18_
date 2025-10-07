# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Champs pour les contrôles qualité
    quality_alert_qty1 = fields.Integer(
        string="Quantité d'Alertes Qualité",
        compute='_compute_quality_alert_qty1',
        store=True
    )
    quality_check_qty1 = fields.Integer(
        string="Quantité de Contrôles Qualité",
        compute='_compute_quality_check_qty1',
        store=True
    )

    @api.depends()
    def _compute_quality_alert_qty1(self):
        for lot in self:
            # Rechercher les alertes qualité liées à ce lot
            alerts = self.env['quality.alert1'].search([('lot_id1', '=', lot.id)])
            lot.quality_alert_qty1 = len(alerts)

    @api.depends()
    def _compute_quality_check_qty1(self):
        for lot in self:
            # Rechercher les contrôles qualité liés à ce lot
            checks = self.env['quality.check1'].search([('lot_id1', '=', lot.id)])
            lot.quality_check_qty1 = len(checks)

    def action_lot_open_quality_alerts1(self):
        """Ouvrir les alertes qualité du lot"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alertes Qualité',
            'res_model': 'quality.alert1',
            'view_mode': 'tree,form',
            'domain': [('lot_id1', '=', self.id)],
        }

    def action_open_quality_checks1(self):
        """Ouvrir les contrôles qualité du lot"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrôles Qualité',
            'res_model': 'quality.check1',
            'view_mode': 'tree,form',
            'domain': [('lot_id1', '=', self.id)],
        }