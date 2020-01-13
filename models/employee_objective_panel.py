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


class EmployeeObjectivePanel(models.Model):

    _inherit = 'employee.objective'
    _name = 'employee.objective.panel'
    _description = 'Panels group employee\'s objectives.'

    employee_ids = fields.One2many(
                                  'hr.employee',
                                  'id',
                                  string="No employee should be selected here..",
                                  compute='_get_employees',
                                  store=True
                                )
    name = fields.Char(
                        string="Panel id",
                        store=True,
                        default=None,
                        required=False
                        )
    monetary_objective = fields.Integer(
                                         string="GENERAL Objective",
                                         compute='_compute_monetary_obj',
                                         readonly=False
                                        )  
    type = fields.Selection([
                             ('so', 'Total Sale Orders'),
                             ('inv', 'Total Invoicing'),
                             ('marg','Revenue Margin')
                             ],
                            index=True,
                            required=False,
                            store=True,
                            default=lambda self: 'marg',
                            help="Type is used to separate different objectives for employees."
                            )
    objective_type = fields.Selection([
                               ('employee', 'For Employee'),
                               ('panel', 'For Panel'),
                               ],
                               index=True,
                               required=True,
                               store=True,
                               default=lambda self: 'panel',
                               help="Is this objective meant to be grouped on a panel?"
                               )
    date_open = fields.Datetime(
                                'Assignation Date',
                                default=fields.Datetime.now,
                                required=False
                                )
    period = fields.Selection([
                               ('custom', 'Custom lapse'),
                               ('day', '1 Day'),
                               ('week', '1 Week'),
                               ('fortnight', '1 Fortnight'),
                               ('month','1 Month'),
                               ('trim','1 Trimester'),
                               ('quad','1 Quadrimester'),
                               ('year','1 Year')],
                               index=True,
                               required=False,
                               store=True,
                               default=lambda self: 'month',
                               help="Assign this employee's objective period."
                               )
    isPanel = fields.Boolean(
        string="Is panel?",
        readonly=True,
        default=True,
        store=True,
        compute='_compute_is_panel'
        )
    objective_ids = fields.One2many(
        'employee.objective',
        'objective_id',
        string="Associated objectives for this panel",
        store=True,
        readonly=False
        )

    @api.depends('objective_type')
    def _compute_is_panel(self):
        for pan in self:

            if pan.objective_type == 'employee':
                pan.isPanel = False
            if pan.objective_type == 'panel':
                pan.isPanel = True

    @api.depends('objective_ids')
    def _get_employees(self):
        for pan in self:
            _employees = []
            for obj in pan.objective_ids:
                _employees.append(obj.employee_id.id)
            pan.employee_ids = pan.env['hr.employee'].browse(_employees)

    @api.depends('objective_ids')
    def _compute_monetary_obj(self):    
        for pan in self:
            #orders_data = pan.env['sale.order']
            _monetary_objective = 0
            for obj in pan.objective_ids:
                _monetary_objective += obj.monetary_objective
            pan.monetary_objective = _monetary_objective

    @api.depends('objective_ids')
    def _compute_planned_revenue(self):
        for pan in self:
            
            #orders_data = pan.env['sale.order']
            _monetary_objective = 0
            _actual_revenue = 0
            _state = True
            _done_percentage = 0
            _type = { pan.objective_ids[0].type } 

            for obj in pan.objective_ids:
                
                """orders_data += orders_data.search([
                                              ('user_id', '=', obj.employee_id.user_id.id),
                                              ('state','in',['sale','done']),
                                              ('date_order','>=',obj.date_open),
                                              ('date_order','<=',obj.date_closed)
                                              ])
                """
                if (obj.type in _type):   #Don't compare apples with oranges
                    _monetary_objective += obj.monetary_objective
                    _actual_revenue += obj.actual_revenue
                    _state = _state and obj.objective_state
                    #IF at least one of the objectives_state is false, then this panel
                    #state, is also false.
            _done_percentage = round((_actual_revenue * 100)/(_monetary_objective or 1),2)
            _logger.info('PANEL DATA : ______ %s , %s , %s , %s %',_monetary_objective,_actual_revenue,_state,_done_percentage)
            pan.monetary_objective = _monetary_objective
            pan.actual_revenue = _actual_revenue
            pan.objective_state = _state
            pan.done_percentage = _done_percentage

            _logger.info('CONTROL TEST DATA : ______ %s , %s , %s , %s %',pan.monetary_objective,pan.actual_revenue,pan.objective_state,pan.done_percentage)

            #pdb.set_trace()


