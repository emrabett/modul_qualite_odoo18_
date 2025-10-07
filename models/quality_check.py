# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import float_round


class QualityCheck1(models.Model):
    _name = "quality.check1"
    _description = "Quality Check"
    _order = "point_id1, id"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    name = fields.Char('Reference', copy=False)
    point_id1 = fields.Many2one(
        'quality.point1', 'Control Point', check_company=True)
    title = fields.Char('Title', compute='_compute_title', store=True, precompute=True, readonly=False)
    quality_state = fields.Selection([
        ('none', 'To do'),
        ('pass', 'Passed'),
        ('fail', 'Failed')], string='Status', tracking=True,
        default='none', copy=False)
    control_date = fields.Datetime('Control Date', tracking=True, copy=False)

    product_id = fields.Many2one(
        'product.product', 'Product', check_company=True,
        domain="[('type', '=', 'consu')]")
    picking_id = fields.Many2one('stock.picking', 'Picking', check_company=True)
    picking_id1 = fields.Many2one('stock.picking', 'Transfert', check_company=True)
    move_line_id1 = fields.Many2one('stock.move.line', 'Ligne de Mouvement', check_company=True)
    production_id1 = fields.Many2one('mrp.production', 'Ordre de Fabrication', check_company=True)
    partner_id = fields.Many2one(
        related='picking_id.partner_id', string='Partner')
    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial',
        check_company=True,
        domain="[('product_id', '=', product_id)]")
    lot_id1 = fields.Many2one(
        'stock.lot', 'Lot/Série',
        check_company=True,
        domain="[('product_id', '=', product_id)]")
    lot_name = fields.Char('Nom du Lot/Série')
    user_id = fields.Many2one('res.users', 'Responsible', tracking=True)
    team_id1 = fields.Many2one(
        'quality.team1', 'Équipe Qualité', required=True, check_company=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, index=True,
        default=lambda self: self.env.company)
    alert_ids = fields.One2many('quality.alert1', 'check_id1', string='Alerts')
    alert_count = fields.Integer('# Quality Alerts', compute="_compute_alert_count")
    note = fields.Html('Note')
    test_type_id = fields.Many2one(
        'quality.point.test_type1', 'Test Type',
        required=True)
    test_type = fields.Char(related='test_type_id.technical_name')
    picture = fields.Binary('Picture', attachment=True)
    additional_note = fields.Text(
        'Additional Note', help="Additional remarks concerning this check.")

    # Champs Enterprise
    failure_message = fields.Html(related='point_id1.failure_message', readonly=True)
    measure = fields.Float('Measure', default=0.0, digits='Quality Tests', tracking=True)
    measure_success = fields.Selection([
        ('none', 'No measure'),
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="Measure Success", compute="_compute_measure_success",
        readonly=True, store=True)
    tolerance_min = fields.Float('Min Tolerance', related='point_id1.tolerance_min', readonly=True)
    tolerance_max = fields.Float('Max Tolerance', related='point_id1.tolerance_max', readonly=True)
    warning_message = fields.Text(compute='_compute_warning_message')
    norm_unit = fields.Char(related='point_id1.norm_unit', readonly=True)
    qty_to_test = fields.Float(compute="_compute_qty_to_test", string="Quantity to Test", help="Quantity of product to test within the lot", digits='Product Unit of Measure')
    qty_tested = fields.Float(string="Quantity Tested", help="Quantity of product tested within the lot", digits='Product Unit of Measure')
    measure_on = fields.Selection([
        ('operation', 'Operation'),
        ('product', 'Product'),
        ('move_line', 'Quantity')], string="Control per", default='product', required=True,
        help="""Operation = One quality check is requested at the operation level.
                  Product = A quality check is requested per product.
                 Quantity = A quality check is requested for each new product quantity registered, with partial quantity checks also possible.""")
    move_line_id = fields.Many2one(
        "stock.move.line",
        "Stock Move Line",
        check_company=True,
        help="In case of Quality Check by Quantity, Move Line on which the Quality Check applies",
        index="btree_not_null",
    )
    move_line_id1 = fields.Many2one(
        "stock.move.line",
        "Ligne de Mouvement",
        check_company=True,
        help="En cas de contrôle qualité par quantité, ligne de mouvement sur laquelle le contrôle qualité s'applique",
        index="btree_not_null",
    )
    failure_location_id = fields.Many2one('stock.location', string="Failure Location")
    lot_name = fields.Char('Lot/Serial Number Name', related='move_line_id.lot_name', store=True)
    lot_line_id = fields.Many2one('stock.lot', store=True, compute='_compute_lot_line_id')
    qty_line = fields.Float(compute='_compute_qty_line', string="Quantity")
    qty_passed = fields.Float('Quantity Passed', help="Quantity of product that passed the quality check", compute='_compute_qty_passed', store=True)
    qty_failed = fields.Float('Quantity Failed', help="Quantity of product that failed the quality check", compute='_compute_qty_failed', store=True)
    qty_tested = fields.Float(string="Quantity Tested", help="Quantity of product tested within the lot", digits='Product Unit of Measure')
    uom_id = fields.Many2one(related='product_id.uom_id', string="Product Unit of Measure")
    show_lot_text = fields.Boolean(compute='_compute_show_lot_text')
    is_lot_tested_fractionally = fields.Boolean(related='point_id1.is_lot_tested_fractionally')
    testing_percentage_within_lot = fields.Float(related="point_id1.testing_percentage_within_lot")
    product_tracking = fields.Selection(related='product_id.tracking')
    # spreadsheet_id = fields.Many2one(
    #     'quality.check.spreadsheet',
    #     domain="[('company_id', 'in', company_ids)]",
    # )
    # spreadsheet_check_cell = fields.Char(
    #     related="spreadsheet_id.check_cell",
    #     readonly=False,
    # )

    # Champ temporaire pour éviter l'erreur RPC
    team_id = fields.Many2one(
        'quality.team1',
        string='Équipe (Compatibilité)',
        related='team_id1',
        help='Champ de compatibilité pour éviter les erreurs'
    )

    def _compute_alert_count(self):
        alert_data = self.env['quality.alert1']._read_group([('check_id1', 'in', self.ids)], ['check_id1'], ['__count'])
        alert_result = {check.id: count for check, count in alert_data}
        for check in self:
            check.alert_count = alert_result.get(check.id, 0)

    def _compute_title(self):
        for check in self:
            check.title = check.point_id1.title

    @api.onchange('point_id1')
    def _onchange_point_id(self):
        if self.point_id1:
            self.team_id1 = self.point_id1.team_id1.id
            self.test_type_id = self.point_id1.test_type_id.id

    def _is_pass_fail_applicable(self):
        """ Return true if do_fail and do_pass can be applied."""
        if self.test_type in ['passfail', 'measure']:
            return True
        return False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quality.check1') or _('New')
            if 'point_id1' in vals and not vals.get('test_type_id'):
                vals['test_type_id'] = self.env['quality.point1'].browse(vals['point_id1']).test_type_id.id
            if 'point_id1' in vals and not vals.get('note'):
                vals['note'] = self.env['quality.point1'].browse(vals['point_id1']).note
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'quality_state' in vals and not vals.get('user_id') or not vals.get('control_date'):
            if vals.get('quality_state') == 'pass':
                self.do_pass()
            elif vals.get('quality_state') == 'fail':
                self.do_fail()
        return res

    def do_fail(self):
        self.write({
            'quality_state': 'fail',
            'user_id': self.env.user.id,
            'control_date': datetime.now()})

    def do_pass(self):
        self.write({'quality_state': 'pass',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now()})

    @api.depends('measure_success')
    def _compute_warning_message(self):
        for rec in self:
            if rec.measure_success == 'fail':
                rec.warning_message = _('You measured %(measure).2f %(unit)s and it should be between %(tolerance_min).2f and %(tolerance_max).2f %(unit)s.',
                    measure=rec.measure, unit=rec.norm_unit, tolerance_min=rec.point_id1.tolerance_min,
                    tolerance_max=rec.point_id1.tolerance_max,
                )
            else:
                rec.warning_message = ''

    @api.depends('move_line_id.quantity')
    def _compute_qty_line(self):
        for qc in self:
            qc.qty_line = qc.move_line_id.quantity if qc.move_line_id else 0

    @api.depends('quality_state')
    def _compute_qty_passed(self):
        for qc in self:
            if qc.quality_state == 'pass':
                qc.qty_passed = 1.0  # Valeur par défaut
            else:
                qc.qty_passed = 0

    @api.depends('quality_state')
    def _compute_qty_failed(self):
        for qc in self:
            if qc.quality_state == 'fail':
                qc.qty_failed = 1.0  # Valeur par défaut
            else:
                qc.qty_failed = 0

    @api.depends('move_line_id.lot_id')
    def _compute_lot_line_id(self):
        for qc in self:
            qc.lot_line_id = qc.move_line_id.lot_id if qc.move_line_id else False
            if qc.lot_line_id and qc._update_lot_from_lot_line():
                qc.lot_id = qc.lot_line_id

    def _update_lot_from_lot_line(self):
        return True

    @api.depends('measure')
    def _compute_measure_success(self):
        for rec in self:
            if rec.point_id1.test_type == 'passfail':
                rec.measure_success = 'none'
            else:
                if rec.measure < rec.point_id1.tolerance_min or rec.measure > rec.point_id1.tolerance_max:
                    rec.measure_success = 'fail'
                else:
                    rec.measure_success = 'pass'

    # Add picture dependency
    @api.depends('picture')
    def _compute_result(self):
        pass

    @api.depends('testing_percentage_within_lot', 'is_lot_tested_fractionally')
    def _compute_qty_to_test(self):
        for qc in self:
            if qc.is_lot_tested_fractionally:
                qc.qty_to_test = float_round(1.0 * qc.testing_percentage_within_lot / 100, precision_rounding=0.01, rounding_method="UP")
            else:
                qc.qty_to_test = 1.0

    @api.depends('product_id')
    def _compute_show_lot_text(self):
        for qc in self:
            # Toujours False car lot_id est commenté
            qc.show_lot_text = False

    def _check_to_unlink(self):
        return True

    def _measure_passes(self):
        self.ensure_one()
        return self.point_id1.tolerance_min <= self.measure <= self.point_id1.tolerance_max

    def do_measure(self):
        self.ensure_one()
        if self._measure_passes():
            return self.do_pass()
        else:
            return self.do_fail()

    def do_alert(self):
        self.ensure_one()
        alert = self.env['quality.alert1'].create({
            'check_id1': self.id,
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            # 'lot_id': self.lot_id.id,  # Commenté car lot_id est commenté
            'user_id': self.user_id.id,
            'team_id1': self.team_id1.id,
            'company_id': self.company_id.id
        })
        return {
            'name': _('Quality Alert'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.alert1',
            'views': [(self.env.ref('quality_management.quality_alert1_view_form').id, 'form')],
            'res_id': alert.id,
            'context': {'default_check_id1': self.id},
        }

    def action_see_alerts(self):
        self.ensure_one()
        if len(self.alert_ids) == 1:
            return {
                'name': _('Quality Alert'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.alert1',
                'views': [(self.env.ref('quality_management.quality_alert1_view_form').id, 'form')],
                'res_id': self.alert_ids.ids[0],
                'context': {'default_check_id1': self.id},
            }
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("quality_management.action_quality_alert1")
            action['domain'] = [('id', 'in', self.alert_ids.ids)]
            action['context'] = dict(self._context, default_check_id1=self.id)
            return action

    def action_open_quality_check_wizard1(self, current_check_id=None):
        check_ids = sorted(self.ids)
        action = self.env["ir.actions.actions"]._for_xml_id("quality_management.action_quality_check_wizard1")
        check_id = self.browse(current_check_id or check_ids[0])
        action['name'] = check_id._get_check_action_name()
        action['context'] = self.env.context.copy()
        action['context'].update({
            'default_check_ids': check_ids,
            'default_current_check_id': check_id.id,
            'default_qty_tested': check_id.qty_to_test,
        })
        return action

    def action_open_spreadsheet(self):
        # Fonctionnalité désactivée car spreadsheet_id est commenté
        return {'type': 'ir.actions.act_window_close'}

    def _create_spreadsheet_from_template(self):
        # Fonctionnalité désactivée car spreadsheet_template_id est commenté
        return False

    def unlink(self):
        # if self.spreadsheet_id:
        #     self.spreadsheet_id.unlink()
        return super().unlink()

    def _can_move_line_to_failure_location(self):
        self.ensure_one()
        return False  # Désactivé car move_line_id est commenté

    def _move_line_to_failure_location(self, failure_location_id, failed_qty=None):
        """ This function is used to fail move lines and can optionally:
             - split it into failed and passed qties (i.e. 2 moves w/1 check each)
             - send the failed qty to a failure location
        :param failure_location_id: id of location to send failed qty to
        :param failed_qty: qty failed on check, defaults to None, if None all quantity of the move is failed
        """
        from odoo import Command
        for check in self:
            if not check._can_move_line_to_failure_location():
                continue
            failed_qty = failed_qty or check.move_line_id.quantity
            move_line = check.move_line_id
            move = move_line.move_id
            move.picked = True
            dest_location = failure_location_id or move_line.location_dest_id.id
            if failed_qty == move_line.quantity:
                move_line.location_dest_id = dest_location
                if move_line.quantity == move.quantity:
                    move.location_dest_id = dest_location
                return
            move_line.quantity -= min(failed_qty, move_line.quantity)
            failed_move_line = move_line.with_context(default_check_ids=None, no_checks=True).copy({
                'location_dest_id': dest_location,
                'quantity': failed_qty,
            })
            move.copy({
                'location_dest_id': dest_location,
                'move_dest_ids': move.move_dest_ids,
                'move_orig_ids': move.move_orig_ids,
                'product_uom_qty': 0,
                'state': 'assigned',
                'move_line_ids': [Command.link(failed_move_line.id)],
                'picked': True,
            })
            # switch the checks, check in self should always be the failed one,
            # new check linked to original move line will be passed check
            new_check = self.create(failed_move_line._get_check_values(check.point_id1))
            check.move_line_id = failed_move_line
            check.failure_location_id = dest_location
            new_check.move_line_id = move_line
            new_check.qty_tested = 0
            new_check.do_pass()

    def _get_check_action_name(self):
        self.ensure_one()
        action_name = self.title or "Quality Check"
        if self.product_id:
            action_name += ' : %s' % self.product_id.name
        if self.qty_to_test and self.uom_id:
            action_name += ' - %s %s' % (self.qty_to_test, self.uom_id.name)
        # if self.lot_name or self.lot_line_id:  # Commenté car lot_name et lot_line_id sont commentés
        #     action_name += ' - %s' % (self.lot_name or self.lot_line_id.name)
        return action_name