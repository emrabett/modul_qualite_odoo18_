# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_confirm(self, merge=True, merge_into=False):
        print(f"=== DEBUG _action_confirm ===")
        print(f"Mouvements à confirmer: {len(self)}")
        moves = super(StockMove, self)._action_confirm(merge=merge, merge_into=merge_into)
        print(f"Mouvements confirmés: {len(moves)}")
        moves._create_quality_checks()
        print("Appel de _create_quality_checks_for_mo()")
        print(f"Type de moves: {type(moves)}")
        print(f"Méthode disponible: {hasattr(moves, '_create_quality_checks_for_mo')}")
        try:
            print("=== AVANT APPEL _create_quality_checks_for_mo ===")
            moves._create_quality_checks_for_mo()
            print("=== APRÈS APPEL _create_quality_checks_for_mo ===")
            print("_create_quality_checks_for_mo() terminé avec succès")
        except Exception as e:
            print(f"ERREUR dans _create_quality_checks_for_mo: {e}")
            import traceback
            traceback.print_exc()
        return moves

    def _create_quality_checks(self):
        # Grouper les mouvements par picking. Utiliser pour générer les contrôles qualité manquants.
        pick_moves = defaultdict(lambda: self.env['stock.move'])
        for move in self:
            if move.picking_id and not move.scrapped:
                pick_moves[move.picking_id] |= move
        check_vals_list = self._create_operation_quality_checks(pick_moves)
        for picking, moves in pick_moves.items():
            # Contrôles qualité par produit
            quality_points_domain = self.env['quality.point1']._get_domain(moves.product_id, picking.picking_type_id, measure_on='product')
            quality_points = self.env['quality.point1'].sudo().search(quality_points_domain)

            if not quality_points:
                continue
            picking_check_vals_list = quality_points._get_checks_values(moves.product_id, picking.company_id.id, existing_checks=picking.sudo().check_ids1 if hasattr(picking, 'check_ids1') else self.env['quality.check1'])
            for check_value in picking_check_vals_list:
                check_value.update({
                    'picking_id1': picking.id,
                })
            check_vals_list += picking_check_vals_list
        self.env['quality.check1'].sudo().create(check_vals_list)

    def _create_operation_quality_checks(self, pick_moves):
        check_vals_list = []
        for picking, moves in pick_moves.items():
            quality_points_domain = self.env['quality.point1']._get_domain(moves.product_id, picking.picking_type_id, measure_on='operation')
            quality_points = self.env['quality.point1'].sudo().search(quality_points_domain)
            for point in quality_points:
                if point.check_execute_now():
                    check_vals_list.append({
                        'point_id1': point.id,
                        'team_id1': point.team_id1.id,
                        'measure_on': 'operation',
                        'picking_id1': picking.id,
                    })
        return check_vals_list

    def _action_cancel(self):
        res = super()._action_cancel()

        to_unlink = self.env['quality.check1'].sudo()
        is_product_canceled = defaultdict(lambda: True)
        # Vérifier si le picking a des contrôles qualité (seulement pour les OF)
        if hasattr(self.picking_id, 'check_ids1'):
            for qc in self.picking_id.sudo().check_ids1:
                if qc.quality_state != 'none':
                    continue
                if (qc.picking_id1, qc.product_id) not in is_product_canceled:
                    for move in qc.picking_id1.move_ids:
                        is_product_canceled[(move.picking_id, move.product_id)] &= move.state == 'cancel'
                if is_product_canceled[(qc.picking_id1, qc.product_id)]:
                    to_unlink |= qc
        to_unlink.unlink()

        return res

    def _create_quality_checks_for_mo(self):
        """Créer les contrôles qualité pour les ordres de fabrication"""
        check_vals_list = []
        productions_done = set()
        
        for move in self:
            if move.production_id and not move.scrapped and move.production_id.id not in productions_done:
                production = move.production_id
                productions_done.add(production.id)
                
                # Chercher TOUS les points de contrôle qualité actifs
                quality_points = self.env['quality.point1'].sudo().search([
                    ('active', '=', True),
                    '|', ('state', '=', False), ('state', '=', 'active'),  # Accepter aussi si pas de state défini
                    ('measure_frequency_type', '!=', 'on_demand'),
                ])
                
                for point in quality_points:
                    # Vérifier si le point s'applique au produit de l'OF
                    if point.product_ids:
                        if production.product_id not in point.product_ids:
                            continue
                    
                    # Vérifier si le point doit être exécuté maintenant
                    if point.check_execute_now():
                        check_vals = {
                            'point_id1': point.id,
                            'team_id1': point.team_id1.id if point.team_id1 else False,
                            'product_id': production.product_id.id,
                            'production_id1': production.id,
                            'measure_on': point.measure_on,
                        }
                        check_vals_list.append(check_vals)
        
        if check_vals_list:
            self.env['quality.check1'].sudo().create(check_vals_list)

    def _search_quality_points1(self, product_id, picking_type_id, measure_on):
        quality_points_domain = self.env['quality.point1']._get_domain(product_id, picking_type_id, measure_on=measure_on)
        quality_points_domain = self.env['quality.point1']._get_domain_for_production(quality_points_domain)
        return self.env['quality.point1'].sudo().search(quality_points_domain)

    def _create_quality_checks_for_mo(self):
        print(f"=== NOUVELLE VERSION CHARGÉE ===")
        print(f"=== DEBUG _create_quality_checks_for_mo DEBUT ===")
        try:
            print(f"=== DEBUG _create_quality_checks_for_mo - DANS TRY ===")
            # Grouper les mouvements par ordre de fabrication. Utiliser pour générer les contrôles qualité manquants.
            mo_moves = defaultdict(lambda: self.env['stock.move'])
            check_vals_list = []
            print(f"=== DEBUG _create_quality_checks_for_mo ===")
            print(f"Mouvements à traiter: {len(self)}")
            for move in self:
                if move.production_id and not move.scrapped:
                    mo_moves[move.production_id] |= move
                    print(f"  Mouvement {move.id} -> OF {move.production_id.name}")
            
            print(f"OF trouvés: {len(mo_moves)}")

            # QC de type produit
            for production, moves in mo_moves.items():
                # Utiliser le premier mouvement pour obtenir le produit
                first_move = moves[0] if moves else None
                if not first_move:
                    continue
                    
                print(f"  Recherche points pour produit {first_move.product_id.name} (ID: {first_move.product_id.id})")
                quality_points = self._search_quality_points1(first_move.product_id, production.picking_type_id, 'product')
                print(f"  Points trouvés (produit): {len(quality_points)}")

                # Puisque les lignes de mouvement sont créées trop tard pour le produit fabriqué, nous créons directement le QC de type move_line ici, en excluant les sous-produits
                quality_points_lot_type = self._search_quality_points1(production.product_id, production.picking_type_id, 'move_line')
                print(f"  Points trouvés (move_line): {len(quality_points_lot_type)}")

                quality_points = quality_points | quality_points_lot_type
                print(f"  Total points: {len(quality_points)}")
                if not quality_points:
                    print(f"  Aucun point trouvé pour OF {production.name}")
                    continue
                mo_check_vals_list = quality_points._get_checks_values(first_move.product_id, production.company_id.id, existing_checks=production.sudo().check_ids1)
                for check_value in mo_check_vals_list:
                    check_value.update({
                        'production_id1': production.id,
                    })
                check_vals_list += mo_check_vals_list

            # QC de type opération
            for production, moves in mo_moves.items():
                quality_points_operation = self._search_quality_points1(self.env['product.product'], production.picking_type_id, 'operation')

                for point in quality_points_operation:
                    if point.check_execute_now():
                        check_vals_list.append({
                            'point_id1': point.id,
                            'team_id1': point.team_id1.id,
                            'measure_on': 'operation',
                            'production_id1': production.id,
                        })

            print(f"Contrôles à créer: {len(check_vals_list)}")
            if check_vals_list:
                self.env['quality.check1'].sudo().create(check_vals_list)
                print(f"Contrôles créés avec succès!")
            else:
                print("Aucun contrôle à créer")
        except Exception as e:
            print(f"ERREUR dans _create_quality_checks_for_mo: {e}")
            import traceback
            traceback.print_exc()
