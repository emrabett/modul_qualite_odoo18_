# Module de Gestion de la Qualité - Version Personnelle

## Description
Ce module fournit une solution complète de gestion de la qualité pour Odoo 18.0 Community, entièrement indépendante des modules Enterprise.

## Fonctionnalités

### Modèles Principaux
- **quality.plan1** : Plans de contrôle qualité
- **quality.point1** : Points de contrôle avec différents types de tests
- **quality.check1** : Contrôles qualité avec workflow complet
- **quality.alert1** : Alertes qualité et gestion des non-conformités
- **quality.team1** : Équipes qualité et gestion des compétences

### Types de Tests Supportés
- **Mesure** : Tests avec tolérances et normes
- **Contrôle Visuel** : Évaluation visuelle
- **Oui/Non** : Tests binaires
- **Réussi/Échoué** : Tests de conformité
- **Photo** : Contrôles avec images
- **Texte** : Observations textuelles

### Fonctionnalités Avancées
- Workflow avec états et transitions
- Système de permissions et groupes
- Statistiques de performance
- Gestion des équipes et responsables
- Alertes automatiques
- Tableaux de bord interactifs

## Installation

1. Copiez le module dans votre dossier addons
2. Redémarrez Odoo
3. Activez le mode développeur
4. Installez le module "Gestion de la Qualité - Module Personnel"

## Structure du Module

```
quality_management/
├── models/
│   ├── quality_plan.py      # Plans de contrôle
│   ├── quality_point.py     # Points de contrôle
│   ├── quality_check.py     # Contrôles qualité
│   ├── quality_alert.py     # Alertes qualité
│   └── quality_team.py      # Équipes qualité
├── views/
│   ├── quality_plan_views.xml
│   ├── quality_point_views.xml
│   ├── quality_check_views.xml
│   ├── quality_alert_views.xml
│   ├── quality_team_views.xml
│   └── quality_menu_views.xml
├── security/
│   ├── quality_security.xml
│   └── ir.model.access.csv
└── data/
    └── quality_data.xml
```

## Utilisation

1. **Créer une équipe qualité** : Configuration > Équipes Qualité
2. **Définir des points de contrôle** : Contrôles Qualité > Points de Contrôle
3. **Créer des plans de contrôle** : Configuration > Plans de Contrôle
4. **Exécuter des contrôles** : Contrôles Qualité > Contrôles Qualité
5. **Gérer les alertes** : Contrôles Qualité > Alertes Qualité

## Caractéristiques Techniques

- **Architecture** : Complètement indépendante d'Enterprise
- **Modèles** : Avec suffixes pour éviter les conflits
- **Compatibilité** : Odoo 18.0 Community
- **Licence** : LGPL-3
- **Dépendances** : base, mail

## Support

Pour toute question ou support, contactez l'équipe de développement.
