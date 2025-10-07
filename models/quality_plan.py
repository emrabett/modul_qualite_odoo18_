# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class QualityPlan1(models.Model):
    """Plan de contrôle qualité (version personnalisée)"""
    _name = 'quality.plan1'
    
    _description = 'Plan de Contrôle Qualité (version personnalisée)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nom du Plan',
        required=True,
        tracking=True,
        help='Nom du plan de contrôle qualité'
    )
    
    active = fields.Boolean(
        default=True,
        help='Actif/Inactif'
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif')
    ], string='État', default='draft', tracking=True)
    
    plan_type = fields.Selection([
        ('reception', 'Réception'),
        ('delivery', 'Livraison'),
        ('production', 'Production'),
        ('stock', 'Stock'),
        ('custom', 'Personnalisé')
    ], string='Type de Plan', required=True, tracking=True)
    
    product_id = fields.Many2one(
        'product.product',
        string='Produit',
        help='Produit spécifique pour ce plan'
    )
    
    product_category_id = fields.Many2one(
        'product.category',
        string='Catégorie Produit',
        help='Catégorie de produits pour ce plan'
    )
    
    frequency = fields.Selection([
        ('all_lots', 'Tous les lots'),
        ('random', 'Aléatoire'),
        ('periodic', 'Périodique'),
        ('on_demand', 'Sur demande')
    ], string='Fréquence', required=True, default='all_lots', tracking=True)
    
    frequency_value = fields.Integer(
        string='Valeur Fréquence',
        help='Valeur pour la fréquence (ex: pourcentage pour aléatoire, jours pour périodique)'
    )
    
    # Champ calculé pour les vues
    check_count = fields.Integer(
        string='Nombre de Contrôles',
        compute='_compute_check_count',
        help='Nombre de contrôles associés à ce plan'
    )
    
    def _compute_check_count(self):
        """Calcule le nombre de contrôles associés"""
        for plan in self:
            if plan.team_id1:
                plan.check_count = self.env['quality.check1'].search_count([
                    ('team_id1', '=', plan.team_id1.id)
                ])
            else:
                plan.check_count = 0
    
    description = fields.Text(
        string='Description',
        help='Description détaillée du plan'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
        required=True
    )
    
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    team_id1 = fields.Many2one(
        'quality.team1',
        string='Équipe Qualité',
        help='Équipe responsable de ce plan'
    )
    
    # Champ temporaire pour éviter l'erreur RPC
    team_id = fields.Many2one(
        'quality.team1',
        string='Équipe (Compatibilité)',
        related='team_id1',
        help='Champ de compatibilité pour éviter les erreurs'
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif')
    ], string='État', default='draft', tracking=True)
    
    @api.constrains('product_id', 'product_category_id')
    def _check_product_configuration(self):
        """Vérifie la configuration produit"""
        for plan in self:
            if plan.product_id and plan.product_category_id:
                raise ValidationError(_(
                    'Vous ne pouvez pas sélectionner à la fois un produit et une catégorie de produit.'
                ))
    
    def action_activate(self):
        """Active le plan de contrôle"""
        self.write({'state': 'active'})
    
    def action_inactivate(self):
        """Désactive le plan de contrôle"""
        self.write({'state': 'inactive'})
    
    def action_draft(self):
        """Remet en brouillon"""
        self.write({'state': 'draft'})
    
    def copy(self, default=None):
        """Copie le plan avec un nouveau nom"""
        default = dict(default or {})
        default['name'] = _('%s (Copie)') % self.name
        return super().copy(default)
    
    @api.model
    def get_dashboard_data(self):
        """Récupère les données pour le dashboard qualité"""
        try:
            # Statistiques des plans de qualité
            total_plans = self.search_count([])
            active_plans = self.search_count([('state', '=', 'active')])
            draft_plans = self.search_count([('state', '=', 'draft')])
            inactive_plans = self.search_count([('state', '=', 'inactive')])
            
            # Plans par type
            plans_by_type = {}
            for plan_type in ['reception', 'production', 'stock', 'custom']:
                plans_by_type[plan_type] = self.search_count([('plan_type', '=', plan_type)])
            
            # Plans par fréquence
            plans_by_frequency = {}
            for frequency in ['all_lots', 'random', 'periodic', 'on_demand']:
                plans_by_frequency[frequency] = self.search_count([('frequency', '=', frequency)])
            
            return {
                'metrics': {
                    'total_plans': total_plans,
                    'active_plans': active_plans,
                    'draft_plans': draft_plans,
                    'inactive_plans': inactive_plans,
                    'plans_by_type': plans_by_type,
                    'plans_by_frequency': plans_by_frequency,
                },
                'status': 'success'
            }
        except Exception as e:
            return {
                'metrics': {},
                'status': 'error',
                'message': str(e)
            }
    
    def action_activate(self):
        """Active le plan de contrôle"""
        for record in self:
            record.state = 'active'
            record.active = True
    
    def action_inactivate(self):
        """Désactive le plan de contrôle"""
        for record in self:
            record.state = 'inactive'
            record.active = False
    
    def action_draft(self):
        """Remet le plan en brouillon"""
        for record in self:
            record.state = 'draft'
            record.active = False
