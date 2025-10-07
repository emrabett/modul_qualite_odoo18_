# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Champs pour les contrôles qualité
    quality_check_todo1 = fields.Boolean(
        string="Contrôles Qualité à Faire",
        compute='_compute_quality_check_data1',
        store=True
    )
    quality_check_fail1 = fields.Boolean(
        string="Contrôles Qualité Échoués",
        compute='_compute_quality_check_data1',
        store=True
    )
    check_count1 = fields.Integer(
        string="Nombre de Contrôles Qualité",
        compute='_compute_quality_check_data1',
        store=True
    )
    quality_alert_count1 = fields.Integer(
        string="Nombre d'Alertes Qualité",
        compute='_compute_quality_check_data1',
        store=True
    )
    check_ids1 = fields.One2many(
        'quality.check1',
        'picking_id1',
        string="Contrôles Qualité"
    )

    @api.depends('check_ids1.quality_state')
    def _compute_quality_check_data1(self):
        for picking in self:
            picking.quality_check_todo1 = any(
                check.quality_state == 'none' 
                for check in picking.check_ids1
            )
            picking.quality_check_fail1 = any(
                check.quality_state == 'fail' 
                for check in picking.check_ids1
            )
            picking.check_count1 = len(picking.check_ids1)
            picking.quality_alert_count1 = self.env['quality.alert1'].search_count([
                ('picking_id1', '=', picking.id)
            ])

    def check_quality1(self):
        """Ouvrir le wizard de contrôle qualité"""
        self.ensure_one()
        checks = self.check_ids1.filtered(lambda x: x.quality_state == 'none')
        if checks:
            return checks.action_open_quality_check_wizard()
        return False

    def button_quality_alert1(self):
        """Créer une alerte qualité"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerte Qualité',
            'res_model': 'quality.alert1',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id1': self.id,
            }
        }

    def open_quality_alert_picking1(self):
        """Ouvrir les alertes qualité du picking"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alertes Qualité',
            'res_model': 'quality.alert1',
            'view_mode': 'list,form',
            'domain': [('picking_id1', '=', self.id)],
        }

    def action_open_quality_check_picking1(self):
        """Ouvrir les contrôles qualité du picking"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrôles Qualité',
            'res_model': 'quality.check1',
            'view_mode': 'list,form',  # Changé de 'tree,form' à 'list,form'
            'domain': [('picking_id1', '=', self.id)],
        }

    def _check_qc_status(self):
        """Vérifier le statut des contrôles qualité"""
        self.ensure_one()
        if not self.check_ids1:
            return True  # Pas de contrôles qualité requis
        
        # Vérifier s'il y a des contrôles en attente
        pending_checks = self.check_ids1.filtered(lambda x: x.quality_state == 'none')
        if pending_checks:
            return False  # Des contrôles sont en attente
        
        return True  # Tous les contrôles sont terminés

    def button_validate(self):
        """Surcharger la validation pour vérifier les contrôles qualité"""
        # Vérifier les contrôles qualité avant validation
        for picking in self:
            if not picking._check_qc_status():
                raise UserError(_(
                    
                    'Vous devez compléter les contrôles qualité avant de valider ce transfert.'
                ))
        
        # Appeler la méthode parent
        return super().button_validate()