# -*- coding: utf-8 -*-

{
    'name': 'Gestion de la Qualité - Module Personnelllllllll1',
    'version': '18.0.1.0.0',
    'category': 'Quality',
    'summary': 'Module personnel de gestion de la qualité - Version indépendante',
    'description': """
Module Personnel de Gestion de la Qualité
=========================================

Ce module fournit une solution personnalisée et indépendante pour la gestion de la qualité dans Odoo.

**Fonctionnalités Principales :**
- Plans de contrôle qualité personnalisés
- Points de contrôle avec types de tests variés
- Contrôles qualité avec workflow complet
- Alertes qualité et gestion des non-conformités
- Équipes qualité et gestion des compétences
- Tableaux de bord interactifs
- Système de permissions et groupes

**Caractéristiques :**
- Architecture complètement indépendante d'Enterprise
- Modèles avec suffixes pour éviter les conflits
- Interface utilisateur moderne et intuitive
- Workflow avec états et transitions
- Système de permissions et groupes
- Intégration avec le système de messagerie Odoo
- Support multilingue
- Compatible avec Odoo 18.0

**Modules Intégrés :**
- Produits et catégories
- Utilisateurs et équipes
- Système de séquences personnalisées
    """,
    'author': 'Votre Nom',
    'website': 'https://www.votresite.com',
    'depends': [
        'base',
        'mail',
        'stock',
        'mrp',
    ],
    'data': [
        'security/quality_security.xml',
        'security/ir.model.access.csv',
        'data/quality_data.xml',
        'data/quality_test_types.xml',
        'data/quality_points_demo.xml',
        # 'data/quality_points_by_operation.xml',
        'data/quality_teams.xml',
        'data/quality_plans.xml',
        'data/quality_alert_stages.xml',
        'data/quality_tags.xml',
        'views/quality_check_views.xml',
        'views/quality_alert_views.xml',
        'views/quality_alert_stage_views.xml',
        'views/quality_tag_views.xml',
        'views/quality_spreadsheet_views.xml',
        'views/quality_plan_views.xml',
        'views/quality_point_views.xml',
        'views/quality_team_views.xml',
        'views/stock_picking_views.xml',  # Désactivé - erreurs Bootstrap
        'views/stock_move_line_views.xml',  # Désactivé - erreurs Bootstrap  
        'views/stock_lot_views.xml',  # Désactivé - erreurs Bootstrap
        'views/mrp_production_views.xml',
        'views/wizard_quality_check_views.xml',
        'views/wizard_on_demand_quality_check_views.xml',
        'wizard/quality_check_wizard_views.xml',
        'views/quality_menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {},
}
