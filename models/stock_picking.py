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
            # Debug : Vérifier les valeurs
            print(f"DEBUG - Checks trouvés: {len(checks)}")
            for check in checks:
                print(f"DEBUG - Check {check.id}: quality_state={check.quality_state}, test_type={check.test_type}")
            return checks.action_open_quality_check_wizard1()
        return False

    def button_quality_alert1(self):
        """Créer une alerte qualité"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerte Qualité',
            'res_model': 'quality.alert1',  # ✅ Avec suffixe "1"
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id1': self.id,  # ✅ Avec suffixe "1"
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

    def action_open_on_demand_quality_check1(self):
        """Ouvrir le wizard de contrôle qualité à la demande"""
        self.ensure_one()
        return {
            'name': 'Contrôle Qualité à la Demande',
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check.on.demand1',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id1': self.id,
            }
        }

    # ✅ Méthode personnalisée - GARDER le suffixe "1"
    def _check_qc_status1(self):
        """Vérifier le statut des contrôles qualité"""
        self.ensure_one()
        if not self.check_ids1:
            return True
        pending_checks = self.check_ids1.filtered(lambda x: x.quality_state == 'none')
        if pending_checks:
            return False
        return True

    # ✅ NE PAS renommer - méthode standard Odoo
    def button_validate(self):
        """Surcharger la validation pour vérifier les contrôles qualité"""
        for picking in self:
            if not picking._check_qc_status1():  # ✅ Appel méthode personnalisée avec "1"
                raise UserError(_(
                    'Vous devez compléter les contrôles qualité avant de valider ce transfert.'
                ))
        return super().button_validate()  # ✅ Appel méthode parent SANS "1"