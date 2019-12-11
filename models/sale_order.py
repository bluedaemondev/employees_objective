# -*- coding: utf-8 -*-
# EYNES- Ingenieria de software - 2019. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
import logging
import datetime  
from datetime import timedelta 

import pdb

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def _update_objective_data(self):
      for so in self:
          obj_env = so.env['employee.objective']
          related_data = obj_env.search([])
          for obj in related_data:
              obj.compute_planned_revenue()

          _logger.info('Debugging, , _update_objective_data')