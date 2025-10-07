# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    # ✅ ENLEVER le "1"
    def _action_confirm(self, merge=True, merge_into=False):
        moves = super(StockMove, self)._action_confirm(merge=merge, merge_into=merge_into)
        moves._create_quality_checks1()  # ✅ Garder le "1" ici
        moves._create_quality_checks_for_mo1()  # ✅ Garder le "1" ici
        return moves

    # ✅ Méthode personnalisée - GARDER le suffixe "1"
    def _create_quality_checks1(self):
        # Grouper les mouvements par picking. Utiliser pour générer les contrôles qualité manquants.
        pick_moves = defaultdict(lambda: self.env['stock.move'])
        for move in self:
            if move.picking_id and not move.scrapped:
                pick_moves[move.picking_id] |= move
        check_vals_list = self._create_operation_quality_checks1(pick_moves)
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

    # ✅ Méthode personnalisée - GARDER le suffixe "1"
    def _create_operation_quality_checks1(self, pick_moves):
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

    # ✅ ENLEVER le "1"
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

    # ✅ Méthode personnalisée - GARDER le suffixe "1"
    def _create_quality_checks_for_mo1(self):
        """Créer les contrôles qualité pour les ordres de fabrication"""
        print(f"=== NOUVELLE VERSION CHARGÉE ===")
        print(f"=== DEBUG _create_quality_checks_for_mo1 DEBUT ===")
        try:
            print(f"=== DEBUG _create_quality_checks_for_mo1 - DANS TRY ===")
            # Grouper les mouvements par ordre de fabrication. Utiliser pour générer les contrôles qualité manquants.
            mo_moves = defaultdict(lambda: self.env['stock.move'])
            check_vals_list = []
            print(f"=== DEBUG _create_quality_checks_for_mo1 ===")
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
            print(f"ERREUR dans _create_quality_checks_for_mo1: {e}")
            import traceback
            traceback.print_exc()

    # ✅ Méthode personnalisée - GARDER le suffixe "1"
    def _search_quality_points1(self, product_id, picking_type_id, measure_on):
        quality_points_domain = self.env['quality.point1']._get_domain(product_id, picking_type_id, measure_on=measure_on)
        quality_points_domain = self.env['quality.point1']._get_domain_for_production(quality_points_domain)
        return self.env['quality.point1'].sudo().search(quality_points_domain)
