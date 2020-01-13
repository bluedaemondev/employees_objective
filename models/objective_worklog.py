# -*- coding: utf-8 -*-
# EYNES- Ingenieria de software - 2019. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
import logging
import datetime  
from datetime import timedelta 

_logger = logging.getLogger(__name__)

class ObjectiveWorklog(models.Model):

    _name = "objective.worklog"
    _description = 'Amount of hours and other info related to an employee\'s objective'

    name = fields.Char(
    	                'Name',
    	                required=False,
    	                store=True
    	                )
    date_log = fields.Datetime(
    	                       'Assignation Date',
                               default=fields.Datetime.now,
                               store=True,
                               readonly=True
                               )
    amount_time = fields.Float(
                                'Amount in hours invested',
    	                        default=0.0,
    	                        store=True
    	                        )
    notes = fields.Text(
    	                'Additional notes',
    	                store=True
    	                )

    objective_id = fields.Many2one(
    	                            'employee.objective',
    	                            string="Current objective",
    	                            store=True
    	                            )