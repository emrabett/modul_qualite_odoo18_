# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv.expression import OR


class QualityAlert1(models.Model):
    _name = "quality.alert1"
    _description = "Quality Alert"
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _check_company_auto = True

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        team_id = self.env.context.get('default_team_id1')
        if not team_id and self.env.context.get('active_model') == 'quality.team1' and\
                self.env.context.get('active_id'):
            team_id = self.env['quality.team1'].browse(self.env.context.get('active_id')).exists().id
        domain = [('team_ids', '=', False)]
        if team_id:
            domain = OR([domain, [('team_ids', 'in', team_id)]])
        return self.env['quality.alert.stage1'].search(domain, limit=1).id

    def _get_default_team_id(self):
        company_id = self.company_id.id or self.env.context.get('default_company_id', self.env.company.id)
        domain = ['|', ('company_id', '=', company_id), ('company_id', '=', False)]
        return self.team_id1._get_quality_team(domain)

    name = fields.Char('Name', default=lambda self: _('New'), copy=False)
    title = fields.Char('Title')
    description = fields.Html('Description')
    stage_id1 = fields.Many2one(
        'quality.alert.stage1', 'Stage', ondelete='restrict',
        group_expand='_read_group_stage_ids',
        default=lambda self: self._get_default_stage_id(),
        domain="['|', ('team_ids', '=', False), ('team_ids', 'in', team_id1)]", tracking=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, index=True,
        default=lambda self: self.env.company)
    reason_id1 = fields.Many2one('quality.reason1', 'Root Cause')
    tag_ids1 = fields.Many2many('quality.tag1', 'quality_alert1_tag_rel', 'alert_id', 'tag_id', string="Tags")
    date_assign = fields.Datetime('Date Assigned')
    date_close = fields.Datetime('Date Closed')
    picking_id1 = fields.Many2one('stock.picking', 'Transfert', check_company=True)
    lot_id1 = fields.Many2one('stock.lot', 'Lot/Série', check_company=True)
    production_id1 = fields.Many2one('mrp.production', 'Ordre de Fabrication', check_company=True)
    action_corrective = fields.Html('Corrective Action')
    action_preventive = fields.Html('Preventive Action')
    user_id = fields.Many2one('res.users', 'Responsible', tracking=True, default=lambda self: self.env.user)
    team_id1 = fields.Many2one(
        'quality.team1', 'Team', required=True, check_company=True,
        default=lambda x: x._get_default_team_id())
    partner_id = fields.Many2one('res.partner', 'Vendor', check_company=True)
    check_id1 = fields.Many2one('quality.check1', 'Check', check_company=True)
    date_alert = fields.Datetime('Date Alert')
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product', check_company=True,
        domain="[('type', '=', 'consu')]")
    product_id = fields.Many2one(
        'product.product', 'Product Variant',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]")
    # lot_id = fields.Many2one(
    #     'stock.lot', 'Lot', check_company=True,
    #     domain="['|', ('product_id', '=', product_id), ('product_id.product_tmpl_id', '=', product_tmpl_id)]")
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string='Priority',
        index=True)

    # Champ temporaire pour éviter l'erreur RPC
    team_id = fields.Many2one(
        'quality.team1',
        string='Équipe (Compatibilité)',
        related='team_id1',
        help='Champ de compatibilité pour éviter les erreurs'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quality.alert1') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        res = super(QualityAlert1, self).write(vals)
        if 'stage_id1' in vals and self.stage_id1.done:
            self.write({'date_close': fields.Datetime.now()})
        return res

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        self.product_id = self.product_tmpl_id.product_variant_ids.ids and self.product_tmpl_id.product_variant_ids.ids[0]

    @api.onchange('team_id1')
    def onchange_team_id(self):
        if self.team_id1:
            self.company_id = self.team_id1.company_id or self.env.company

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """ Only shows the stage related to the current team.
        """
        team_id = self.env.context.get('default_team_id1')
        domain = [('id', 'in', stages.ids)]
        if not team_id and self.env.context.get('active_model') == 'quality.team1' and\
                self.env.context.get('active_id'):
            team_id = self.env['quality.team1'].browse(self.env.context.get('active_id')).exists().id
        if team_id:
            domain = OR([domain, ['|', ('team_ids', '=', False), ('team_ids', 'in', team_id)]])
        elif not stages:
            # if enter here, means we won't get any team_id and stage_id to search
            # so search stage without team_ids instead
            domain = [('team_ids', '=', False)]
        stage_ids = stages.sudo()._search(domain, order=stages._order)
        return stages.browse(stage_ids)

    def action_see_check(self):
        return {
            'name': _('Quality Check'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'quality.check1',
            'target': 'current',
            'res_id': self.check_id1.id,
        }

    @api.depends('name', 'title')
    def _compute_display_name(self):
        for record in self:
            name = record.name + ' - ' + record.title if record.title else record.name
            record.display_name = name

    @api.model
    def name_create(self, name):
        """ Create an alert with name_create should use prepend the sequence in the name """
        record = self.create({
            'title': name,
        })
        return record.id, record.display_name

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Override, used with creation by email alias. The purpose of the override is
        to use the subject for title and body for description instead of the name.
        """
        # We need to add the name in custom_values or it will use the subject.
        custom_values['name'] = self.env['ir.sequence'].next_by_code('quality.alert1') or _('New')
        if msg_dict.get('subject'):
            custom_values['title'] = msg_dict['subject']
        if msg_dict.get('body'):
            custom_values['description'] = msg_dict['body']
        return super(QualityAlert1, self).message_new(msg_dict, custom_values)