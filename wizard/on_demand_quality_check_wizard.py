# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QualityCheckOnDemand(models.TransientModel):
    _name = 'quality.check.on.demand1'
    _description = "Assistant pour Contrôle Qualité à la Demande"

    picking_id1 = fields.Many2one('stock.picking', string='Transfert')
    production_id1 = fields.Many2one('mrp.production', string='Ordre de Fabrication')
    product_id = fields.Many2one('product.product', string='Produit',
                                 domain="[('id', 'in', allowed_product_ids)]")
    quality_point_id1 = fields.Many2one('quality.point1', string='Point de Contrôle Qualité',
                                       domain="[('id', 'in', allowed_quality_point_ids)]", required=True)
    lot_id1 = fields.Many2one('stock.lot', string='Lot/Numéro de Série',
                             help="Si vous voulez spécifier un lot/numéro de série avant la validation du transfert,\
                                créez un nouveau lot ici à partir de ce champ avec le même nom exact de lot de la ligne de mouvement pour laquelle vous voulez ajouter un contrôle.\
                                Si vous voulez créer un contrôle pour toutes les lignes de mouvement, laissez ce champ vide.", domain="[('product_id', '=', product_id)]")
    allowed_product_ids = fields.One2many('product.product', compute='_compute_allowed_product_ids')
    allowed_quality_point_ids = fields.One2many('quality.point1', compute='_compute_allowed_quality_point_ids')
    show_lot_number = fields.Boolean(compute='_compute_show_lot_number')
    measure_on = fields.Selection(related='quality_point_id1.measure_on', readonly=True)

    @api.depends('picking_id1', 'picking_id1.move_ids', 'production_id1', 'production_id1.move_raw_ids', 'production_id1.move_finished_ids')
    def _compute_allowed_product_ids(self):
        for wizard in self:
            if wizard.picking_id1:
                wizard.allowed_product_ids = wizard.picking_id1.move_ids.product_id
            elif wizard.production_id1:
                wizard.allowed_product_ids = (wizard.production_id1.move_raw_ids | wizard.production_id1.move_finished_ids).product_id

    @api.depends('picking_id1', 'production_id1', 'product_id', 'allowed_product_ids')
    def _compute_allowed_quality_point_ids(self):
        for wizard in self:
            if wizard.picking_id1:
                domain = self.env['quality.point1']._get_domain(wizard.product_id or wizard.allowed_product_ids, wizard.picking_id1.picking_type_id, on_demand=True)
            elif wizard.production_id1:
                # Pour les ordres de fabrication, utiliser un picking_type_id par défaut
                picking_type = self.env['stock.picking.type'].search([('code', '=', 'mrp_operation')], limit=1)
                domain = self.env['quality.point1']._get_domain(wizard.product_id or wizard.allowed_product_ids, picking_type, on_demand=True)
            else:
                domain = []
            wizard.allowed_quality_point_ids = self.env['quality.point1'].search(domain)

    @api.depends('product_id', 'quality_point_id1')
    def _compute_show_lot_number(self):
        for wizard in self:
            wizard.show_lot_number = wizard.quality_point_id1 and wizard.quality_point_id1.measure_on == 'move_line' and wizard.product_id and wizard.product_id.tracking != 'none'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.quality_point_id1 not in self.allowed_quality_point_ids:
            self.quality_point_id1 = False

    def action_confirm(self):
        self.ensure_one()
        if self.picking_id1 and self.picking_id1.state in ['draft', 'done', 'cancel']:
            raise UserError(_('Vous ne pouvez pas créer de contrôle qualité pour un transfert brouillon, terminé ou annulé.'))
        if self.production_id1 and self.production_id1.state in ['draft', 'done', 'cancel']:
            raise UserError(_('Vous ne pouvez pas créer de contrôle qualité pour un ordre de fabrication brouillon, terminé ou annulé.'))
        self.env['quality.check1'].sudo().create(self._get_check_values())

    def _get_check_values(self):
        check_values_list = []
        check_value = {
            'point_id1': self.quality_point_id1.id,
            'measure_on': self.quality_point_id1.measure_on,
            'team_id1': self.quality_point_id1.team_id1.id,
        }
        
        if self.picking_id1:
            check_value['picking_id1'] = self.picking_id1.id
        if self.production_id1:
            check_value['production_id1'] = self.production_id1.id
            
        if self.quality_point_id1.measure_on != 'operation':
            check_value['product_id'] = self.product_id.id
        if self.quality_point_id1.measure_on == 'move_line':
            if self.lot_id1:
                if self.picking_id1:
                    ml = self.picking_id1.move_line_ids.filtered(lambda ml: ml.product_id == self.product_id and (ml.lot_name == self.lot_id1.name or ml.lot_id == self.lot_id1))
                    if not ml:
                        raise UserError(_('Le lot/numéro de série sélectionné n\'existe pas dans le transfert.'))
                    check_value['move_line_id1'] = ml.id
                else:
                    # Pour les ordres de fabrication, créer un contrôle par ligne de mouvement
                    check_values_list = [{
                        **check_value,
                        'move_line_id1': ml.id,
                    } for ml in self.production_id1.move_raw_ids.filtered(lambda ml: ml.product_id == self.product_id)]
            else:
                if self.picking_id1:
                    check_values_list = [{
                        **check_value,
                        'move_line_id1': ml.id,
                    } for ml in self.picking_id1.move_line_ids.filtered(lambda ml: ml.product_id == self.product_id)]
                else:
                    check_values_list = [{
                        **check_value,
                        'move_line_id1': ml.id,
                    } for ml in self.production_id1.move_raw_ids.filtered(lambda ml: ml.product_id == self.product_id)]
        return check_values_list or [check_value]
