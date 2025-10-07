# -*- coding: utf-8 -*-

from math import sqrt
from dateutil.relativedelta import relativedelta
from datetime import datetime
import random

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class QualityPoint1(models.Model):
    _name = "quality.point1"
    _description = "Quality Control Point"
    _inherit = ['mail.thread']
    _order = "sequence, id"
    _check_company_auto = True

    def _get_default_team_id(self):
        company_id = self.company_id.id or self.env.context.get('default_company_id', self.env.company.id)
        return self.team_id1._get_quality_team(self.env['quality.team1']._check_company_domain(company_id))

    def _get_default_test_type_id(self):
        domain = self._get_type_default_domain()
        return self.env['quality.point.test_type1'].search(domain, limit=1).id
        # Retourner None car le modèle quality.point.test_type1 n'existe pas
        # return None

    name = fields.Char(
        'Reference', copy=False, default=lambda self: _('New'),
        required=True)
    sequence = fields.Integer('Sequence')
    title = fields.Char('Title')
    team_id1 = fields.Many2one(
        'quality.team1', 'Équipe', check_company=True,
        default=_get_default_team_id, required=True)
    product_ids = fields.Many2many(
        'product.product', 'quality_point1_product_rel', 'point_id', 'product_id',
        string='Products', check_company=True,
        domain="[('type', '=', 'consu')]",
        help="Quality Point will apply to every selected Products.")
    product_category_ids = fields.Many2many(
        'product.category', 'quality_point1_product_category_rel', 'point_id', 'category_id',
        string='Product Categories',
        help="Quality Point will apply to every Products in the selected Product Categories.")

    # picking_type_ids = fields.Many2many(
    #     'stock.picking.type', 'quality_point1_picking_type_rel', 'point_id', 'picking_type_id',
    #     string='Operation Types', required=True, check_company=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', 'Responsible',
        domain=lambda self: [('groups_id', 'in', self.env.ref("quality_management.group_quality_user").id), ('share', '=', False)],
        check_company=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif')
    ], string='État', default='draft', tracking=True)
    check_count = fields.Integer(compute="_compute_check_count")
    check_ids = fields.One2many('quality.check1', 'point_id1')
    test_type_id = fields.Many2one('quality.point.test_type1', 'Test Type', help="Defines the type of the quality control point.",
                                  required=True,default=_get_default_test_type_id, tracking=True)
    test_type = fields.Char(related='test_type_id.technical_name', readonly=True)
    note = fields.Html('Note')
    reason = fields.Html('Cause')
    picking_type_ids = fields.Many2many(
        'stock.picking.type', 'quality_point1_picking_type_rel', 'point_id', 'picking_type_id',
        string='Operations', required=True)
    # picking_type_ids = fields.Many2many(
    #     'stock.picking.type', string='Operation Types',
    #     help="Operation types for which this quality point applies")
    # Champs Enterprise
    failure_message = fields.Html('Failure Message')
    failure_location_ids = fields.Many2many('stock.location', 'quality_point1_failure_location_rel', 'point_id', 'location_id', 
                            string="Failure Locations", domain="[('usage', '=', 'internal')]",
                            help="If a quality check fails, a location is chosen from this list for each failed quantity.")
    measure_on = fields.Selection([
        ('operation', 'Operation'),
        ('product', 'Product'),
        ('move_line', 'Quantity')], string="Control par", default='product', required=True,
        help="""Operation = One quality check is requested at the operation level.
                  Product = A quality check is requested per product.
                 Quantity = A quality check is requested for each new product quantity registered, with partial quantity checks also possible.""")
    measure_frequency_type = fields.Selection([
        ('all', 'All'),
        ('random', 'Randomly'),
        ('periodical', 'Periodically'),
        ('on_demand', 'On-demand')], string="Control Frequency",
        default='all', required=True)
    measure_frequency_value = fields.Float('Percentage')
    measure_frequency_unit_value = fields.Integer('Frequency Unit Value')
    measure_frequency_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months')], default="day")
    is_lot_tested_fractionally = fields.Boolean(string="Lot Tested Fractionally", help="Determines if only a fraction of the lot should be tested",
                                                compute="_compute_is_lot_tested_fractionally")
    testing_percentage_within_lot = fields.Float(help="Defines the percentage within a lot that should be tested", default=100)
    norm = fields.Float('Norm', digits='Quality Tests')
    tolerance_min = fields.Float('Min Tolerance', digits='Quality Tests')
    tolerance_max = fields.Float('Max Tolerance', digits='Quality Tests')
    norm_unit = fields.Char('Norm Unit', default=lambda self: 'mm')
    average = fields.Float(compute="_compute_standard_deviation_and_average")
    standard_deviation = fields.Float(compute="_compute_standard_deviation_and_average")
    # spreadsheet_template_id = fields.Many2one(
    #     'quality.spreadsheet.template',
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    # )
    # spreadsheet_check_cell = fields.Char(
    #     related="spreadsheet_template_id.check_cell",
    #     readonly=False,
    # )

    # Champ temporaire pour éviter l'erreur RPC
    team_id = fields.Many2one(
        'quality.team1',
        string='Équipe (Compatibilité)',
        related='team_id1',
        help='Champ de compatibilité pour éviter les erreurs'
    )

    @api.depends('name', 'title')
    @api.depends_context('on_demand_wizard')
    def _compute_display_name(self):
        if 'on_demand_wizard' in self.env.context:
            for record in self:
                record.display_name = f'{record.name} - {record.title}' if record.title else record.name
        else:
            super()._compute_display_name()

    def _compute_check_count(self):
        check_data = self.env['quality.check1']._read_group([('point_id1', 'in', self.ids)], ['point_id1'], ['__count'])
        result = {point.id: count for point, count in check_data}
        for point in self:
            point.check_count = result.get(point.id, 0)

    @api.depends('testing_percentage_within_lot')
    def _compute_is_lot_tested_fractionally(self):
        for point in self:
            point.is_lot_tested_fractionally = point.testing_percentage_within_lot < 100

    def _compute_standard_deviation_and_average(self):
        # The variance and mean are computed by the Welford's method and used the Bessel's
        # correction because are working on a sample.
        for point in self:
            if point.test_type != 'measure':
                point.average = 0
                point.standard_deviation = 0
                continue
            mean = 0.0
            s = 0.0
            n = 0
            for check in point.check_ids.filtered(lambda x: x.quality_state != 'none'):
                n += 1
                delta = check.measure - mean
                mean += delta / n
                delta2 = check.measure - mean
                s += delta * delta2

            if n > 1:
                point.average = mean
                point.standard_deviation = sqrt( s / ( n - 1))
            elif n == 1:
                point.average = mean
                point.standard_deviation = 0.0
            else:
                point.average = 0.0
                point.standard_deviation = 0.0

    @api.onchange('norm')
    def onchange_norm(self):
        if self.tolerance_max == 0.0:
            self.tolerance_max = self.norm

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quality.point1') or _('New')
        return super().create(vals_list)

    def check_execute_now(self):
        self.ensure_one()
        if self.measure_frequency_type == 'all':
            return True
        elif self.measure_frequency_type == 'random':
            return (random.random() < self.measure_frequency_value / 100.0)
        elif self.measure_frequency_type == 'periodical':
            delta = False
            if self.measure_frequency_unit == 'day':
                delta = relativedelta(days=self.measure_frequency_unit_value)
            elif self.measure_frequency_unit == 'week':
                delta = relativedelta(weeks=self.measure_frequency_unit_value)
            elif self.measure_frequency_unit == 'month':
                delta = relativedelta(months=self.measure_frequency_unit_value)
            date_previous = datetime.today() - delta
            checks = self.env['quality.check1'].search([
                ('point_id1', '=', self.id),
                ('create_date', '>=', date_previous.strftime(DEFAULT_SERVER_DATETIME_FORMAT))], limit=1)
            return not(bool(checks))
        return True

    def _get_type_default_domain(self):
        # Retourner un domaine vide car le modèle quality.point.test_type1 n'existe pas
        return []

    def action_see_quality_checks(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("quality_management.action_quality_check1")
        action['domain'] = [('point_id1', '=', self.id)]
        action['context'] = {
            'default_company_id': self.company_id.id,
            'default_point_id1': self.id
        }
        return action

    def action_see_spc_control(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("quality_management.action_quality_check1")
        if self.test_type == 'measure':
            action['context'] = {'group_by': ['name', 'point_id1'], 'graph_measure': ['measure'], 'graph_mode': 'line'}
        action['domain'] = [('point_id1', '=', self.id), ('quality_state', '!=', 'none')]
        return action

    def _get_checks_values(self, products, company_id, existing_checks=False):
        quality_points_list = []
        point_values = []
        if not existing_checks:
            existing_checks = []
        for check in existing_checks:
            point_key = (check.point_id1.id, check.team_id1.id, check.product_id.id)
            quality_points_list.append(point_key)

        for point in self:
            if not point.check_execute_now():
                continue
            point_products = point.product_ids

            if point.product_category_ids:
                point_product_from_categories = self.env['product.product'].search([('categ_id', 'child_of', point.product_category_ids.ids), ('id', 'in', products.ids)])
                point_products |= point_product_from_categories

            if not point.product_ids and not point.product_category_ids:
                point_products |= products

            for product in point_products:
                if product not in products:
                    continue
                point_key = (point.id, point.team_id1.id, product.id)
                if point_key in quality_points_list:
                    continue
                point_values.append({
                    'point_id1': point.id,
                    'measure_on': point.measure_on,
                    'team_id1': point.team_id1.id,
                    'product_id': product.id,
                })
                quality_points_list.append(point_key)

        return point_values

    @api.model
    def _get_domain(self, product_ids, picking_type_id, measure_on=False, on_demand=False):
        """ Helper that returns a domain for quality.point based on the products and picking type
        pass as arguments. It will search for quality point having:
        - No product_ids and no product_category_id
        - At least one variant from product_ids
        - At least one category that is a parent of the product_ids categories

        :param product_ids: the products that could require a quality check
        :type product: :class:`~odoo.addons.product.models.product.ProductProduct`
        :param picking_type_id: the products that could require a quality check
        :type product: :class:`~odoo.addons.stock.models.stock_picking.PickingType`
        :return: the domain for quality point with given picking_type_id for all the product_ids
        :rtype: list
        """
        from odoo.osv.expression import OR
        domain = [('picking_type_ids', 'in', picking_type_id.ids)]
        domain_in_products_or_categs = ['|', ('product_ids', 'in', product_ids.ids), ('product_category_ids', 'parent_of', product_ids.categ_id.ids)]
        domain_no_products_and_categs = [('product_ids', '=', False), ('product_category_ids', '=', False)]
        domain += OR([domain_in_products_or_categs, domain_no_products_and_categs])
        if measure_on:
            domain += [('measure_on', '=', measure_on)]
        domain += [('measure_frequency_type', '=' if on_demand else '!=', 'on_demand')]

        return domain

    def action_activate(self):
        self.write({'state': 'active'})

    def action_inactivate(self):
        self.write({'state': 'inactive'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def _get_domain_for_production(self, quality_points_domain):
        return quality_points_domain