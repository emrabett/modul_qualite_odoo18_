# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Champs et méthodes temporairement commentés pour éviter les erreurs de chargement
    # Ils seront réactivés une fois que les modèles de base sont stables
    pass
