# -*- coding: utf-8 -*-

# Modèles de qualité avec suffixes pour éviter les conflits Enterprise
from . import stock_picking  # Intégration qualité avec stock
from . import stock_move
from . import stock_move_line
from . import stock_lot
from . import mrp_production  # Intégration qualité avec MRP
from . import quality_plan
from . import quality_point
from . import quality_check
from . import quality_team
from . import quality_alert
from . import quality_test_type
from . import quality_reason
from . import quality_tag
from . import quality_alert_stage
from . import quality_spreadsheet_template
from . import quality_check_spreadsheet

