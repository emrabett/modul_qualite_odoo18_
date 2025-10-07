# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    check_ids1 = fields.One2many('quality.check1', 'production_id1', string="Contrôles Personnels")
    check_count1 = fields.Integer('Nombre de contrôles', compute='_compute_check1', store=True)
    quality_check_todo1 = fields.Boolean(compute='_compute_check1', store=True)
    quality_check_fail1 = fields.Boolean(compute='_compute_check1', store=True)
    quality_alert_ids1 = fields.One2many('quality.alert1', "production_id1", string="Alertes")
    quality_alert_count1 = fields.Integer(compute='_compute_quality_alert_count1', store=True)

    # Champs personnalisés avec suffixe 1 pour éviter les conflits avec Enterprise

    @api.depends('quality_alert_ids1')
    def _compute_quality_alert_count1(self):
        for production in self:
            production.quality_alert_count1 = len(production.quality_alert_ids1)

    @api.depends('check_ids1.quality_state')    
    def _compute_check1(self):
        for production in self:
            print(f"=== DEBUG _compute_check1 ===")
            print(f"OF: {production.name}")
            print(f"check_ids1 count: {len(production.check_ids1)}")
            
            # Initialiser les valeurs par défaut pour TOUS les enregistrements
            production.quality_check_fail1 = False
            production.quality_check_todo1 = False
            production.check_count1 = len(production.check_ids1)
            
            # Calculer les valeurs réelles basées sur les contrôles existants
            for check in production.check_ids1:
                if check.quality_state == 'none':
                    production.quality_check_todo1 = True
                elif check.quality_state == 'fail':
                    production.quality_check_fail1 = True
                if production.quality_check_fail1 and production.quality_check_todo1:
                    break
            
            print(f"quality_check_todo1: {production.quality_check_todo1}")
            print(f"quality_check_fail1: {production.quality_check_fail1}")
            print(f"check_count1: {production.check_count1}")

    def _create_quality_checks_if_needed1(self):
        """Créer les contrôles qualité si nécessaire"""
        if self.state in ['confirmed', 'progress', 'to_close']:
            # Vérifier s'il y a déjà des contrôles qualité du module personnel
            personal_checks = self.check_ids1.filtered(lambda c: c.point_id1)
            if not personal_checks:
                (self.move_raw_ids | self.move_finished_ids)._create_quality_checks_for_mo1()

    def button_quality_alert1(self):
        """Créer une alerte qualité pour l'ordre de fabrication"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerte Qualité',
            'res_model': 'quality.alert1',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id1': self.id,
            }
        }

    def pre_button_mark_done1(self):
        res = super().pre_button_mark_done1()
        if isinstance(res, dict) and res.get('type') == 'ir.actions.act_window':
            return res
        is_qc_status_ok = self._check_qc_status1()
        if not is_qc_status_ok:
            raise UserError(_('Opération invalide\n\nVous devez compléter les contrôles qualité dans l\'application Atelier avant de marquer l\'ordre de travail comme terminé.'))
        return res

    def _check_qc_status1(self):
        return 'none' not in self.check_ids1.mapped('quality_state')

    def open_quality_alert_mo1(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("quality_management.action_quality_alert1")
        action['context'] = {
            'default_company_id': self.company_id.id,
            'default_product_id': self.product_id.id,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_production_id1': self.id,
            }
        action['domain'] = [('id', 'in', self.quality_alert_ids1.ids)]
        action['views'] = [(False, 'list'), (False, 'form')]
        if self.quality_alert_count1 == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.quality_alert_ids1.id
        return action

    def check_quality1(self):
        self.ensure_one()
        if float_is_zero(self.qty_producing, precision_rounding=self.product_uom_id.rounding):
            raise UserError(_("Vous ne pouvez pas effectuer de contrôle qualité si la quantité en production est zéro. Veuillez d'abord définir la quantité de production."))
        checks = self.check_ids1.filtered(lambda x: x.quality_state == 'none')
        print(f"=== DEBUG CHECK_QUALITY1 ===")
        print(f"OF: {self.name}")
        print(f"qty_producing: {self.qty_producing}")
        print(f"check_ids1 count: {len(self.check_ids1)}")
        print(f"checks with state=none: {len(checks)}")
        for check in checks:
            print(f"  Contrôle {check.id}: state={check.quality_state}, point={check.point_id1.name if check.point_id1 else 'None'}")
        
        if checks:
            action = checks.action_open_quality_check_wizard1()
            print(f"Action retournée: {action}")
            return action
        else:
            print("Aucun contrôle trouvé avec state=none")
            return False

    def action_cancel1(self):
        res = super(MrpProduction, self).action_cancel1()
        self.sudo().mapped('check_ids1').filtered(lambda x: x.quality_state == 'none').unlink()
        return res

    def action_confirm1(self):
        res = super().action_confirm1()
        # Créer les contrôles qualité seulement si pas déjà créés par le module enterprise
        if not self.check_ids1:
            (self.move_raw_ids | self.move_finished_ids)._create_quality_checks_for_mo1()
        return res


    def _action_confirm_mo_backorders1(self):
        super()._action_confirm_mo_backorders1()
        (self.move_raw_ids | self.move_finished_ids)._create_quality_checks_for_mo1()

    def create_quality_checks1(self):
        """Créer manuellement les contrôles qualité pour un OF"""
        self.ensure_one()
        if self.state in ['draft', 'done', 'cancel']:
            raise UserError(_('Vous ne pouvez pas créer de contrôle qualité pour un ordre de fabrication brouillon, terminé ou annulé.'))
        
        # Supprimer les anciens contrôles qualité personnels s'ils existent
        old_checks = self.check_ids1.filtered(lambda c: c.point_id1)
        old_checks.unlink()
        
        # Chercher tous les points de contrôle qualité actifs
        quality_points = self.env['quality.point1'].sudo().search([
            ('active', '=', True),
            '|', ('state', '=', False), ('state', '=', 'active'),
            ('measure_frequency_type', '!=', 'on_demand'),
        ])
        
        check_vals_list = []
        for point in quality_points:
            
            # Vérifier si le point s'applique au produit de l'OF
            if point.product_ids and self.product_id not in point.product_ids:
                continue
            
            if point.check_execute_now():
                check_vals_list.append({
                    'point_id1': point.id,
                    'team_id1': point.team_id1.id if point.team_id1 else False,
                    'product_id': self.product_id.id,
                    'production_id1': self.id,
                    'measure_on': point.measure_on,
                })
        
        if check_vals_list:
            self.env['quality.check1'].sudo().create(check_vals_list)
            # Forcer la mise à jour de l'interface
            self.invalidate_recordset(['check_ids1', 'quality_check_todo1', 'quality_check_fail1', 'check_count1'])
            
            # Forcer le recalcul manuel des champs
            self.quality_check_fail1 = False
            self.quality_check_todo1 = False
            self.check_count1 = len(self.check_ids1)
            
            # Calculer les valeurs réelles basées sur les contrôles existants
            for check in self.check_ids1:
                if check.quality_state == 'none':
                    self.quality_check_todo1 = True
                elif check.quality_state == 'fail':
                    self.quality_check_fail1 = True
                if self.quality_check_fail1 and self.quality_check_todo1:
                    break
            
            # Debug: Afficher les valeurs après création
            print(f"=== DEBUG APRÈS CRÉATION ===")
            print(f"OF: {self.name}")
            print(f"check_ids1 count: {len(self.check_ids1)}")
            print(f"quality_check_todo1: {self.quality_check_todo1}")
            print(f"quality_check_fail1: {self.quality_check_fail1}")
            print(f"check_count1: {self.check_count1}")
            
            # Debug détaillé des contrôles
            for check in self.check_ids1:
                print(f"  Contrôle {check.id}: state={check.quality_state}, point={check.point_id1.name if check.point_id1 else 'None'}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'{len(check_vals_list)} contrôle(s) qualité créé(s) avec succès !',
                    'type': 'success',
                    'sticky': True,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Aucun point de contrôle qualité applicable trouvé. Vérifiez que le produit {self.product_id.name} correspond aux points de contrôle.',
                    'type': 'warning',
                    'sticky': True,
                }
            }

    def debug_quality_points1(self):
        """Méthode de débogage pour vérifier les points de contrôle"""
        self.ensure_one()
        
        # Chercher tous les points de contrôle qualité
        all_points = self.env['quality.point1'].sudo().search([])
        active_points = self.env['quality.point1'].sudo().search([
            ('active', '=', True),
            '|', ('state', '=', False), ('state', '=', 'active'),
            ('measure_frequency_type', '!=', 'on_demand'),
        ])
        
        debug_info = f"""
=== DÉBOGAGE POINTS DE CONTRÔLE ===
OF: {self.name}
Produit: {self.product_id.name} (ID: {self.product_id.id})

TOUS LES POINTS ({len(all_points)}):
"""
        
        for point in all_points:
            debug_info += f"""
- {point.name} (ID: {point.id})
  • Actif: {point.active}
  • État: {point.state}
  • Fréquence: {point.measure_frequency_type}
  • Produits: {point.product_ids.mapped('name')}
  • Équipe: {point.team_id1.name if point.team_id1 else 'Aucune'}
  • Type: {point.test_type_id.name if point.test_type_id else 'Aucun'}
"""
        
        debug_info += f"""
POINTS APPLICABLES ({len(active_points)}):
"""
        
        for point in active_points:
            applicable = not point.product_ids or self.product_id in point.product_ids
            execute_now = point.check_execute_now()
            debug_info += f"""
- {point.name}
  • Applicable: {applicable}
  • Execute now: {execute_now}
  • Produits du point: {point.product_ids.mapped('name')}
  • Produit OF: {self.product_id.name}
"""
        
        # Afficher les informations de debug dans la notification
        print(f"=== DÉBOGAGE POINTS DE CONTRÔLE ===")
        print(f"OF: {self.name}")
        print(f"Produit: {self.product_id.name} (ID: {self.product_id.id})")
        print(f"Points applicables: {len(active_points)}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Débogage terminé. Vérifiez les logs pour plus de détails. Points trouvés: {len(active_points)}',
                'type': 'info',
                'sticky': True,
            }
        }

    def action_open_on_demand_quality_check1(self):
        self.ensure_one()
        if self.state in ['draft', 'done', 'cancel']:
            raise UserError(_('Vous ne pouvez pas créer de contrôle qualité pour un ordre de fabrication brouillon, terminé ou annulé.'))
        return {
            'name': _('Contrôle Qualité à la Demande'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check1',
            'views': [(self.env.ref('quality_management.quality_check1_view_form').id, 'form')],
            'target': 'new',
            'context': {
                'default_production_id1': self.id,
                'on_demand_wizard': True,
            }
        }
