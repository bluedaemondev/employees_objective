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


class EmployeeObjective(models.Model):

    _name = "employee.objective"
    _description = 'employees objective log. Multiple types and periods are stored.'

    objective_id = fields.Char(
                                  string="Objective index",
                                  compute='_compute_objective_id',
                                  store=True
                                  )
    employee_id = fields.Many2one(
                                  'hr.employee',
                                  string="Employee related to this objective.",
                                  store=True,
                                  default=None,
                                  required=False
                                )
                                
    user_id = fields.Many2one(
                                  'res.users',
                                  string="User",
                                  store=True,
                                  related='employee_id.user_id'
                                )
    name = fields.Char(
                        string="Name",
                        store=True,
                        required=True
                        )
    notes = fields.Text(
                        string="Other Info...",
                        store=True
                        )

    currency = fields.Many2one(
                                'res.currency',
                                string='Currency',
                                store=True
                            )
    monetary_objective = fields.Integer(
                                         string="Monetary Objective",
                                         readonly=False,
                                         compute='_compute_monetary_obj',
                                         required=True,
                                         store=True
                                        )  
    actual_revenue = fields.Integer(
                                    compute='_compute_planned_revenue',
                                    string="Actual revenue",
                                    store=False
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

    objective_state = fields.Boolean(
                                    string="Completed?",
                                    readonly=True,
                                    default=False,
                                    store=True,
                                    compute='_compute_objective_state'
                                    )
    
    date_open = fields.Datetime(
                                'Assignation Date',
                                default=fields.Datetime.now,
                                required=True
                                )
    date_closed = fields.Datetime('Finished Date', copy=False, default=fields.Datetime.now)
    day_close = fields.Float(
                            compute='_compute_deadline',
                            string='Days to Close'
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
                               required=True,
                               store=True,
                               default=lambda self: 'month',
                               help="Assign a period for this objective."
                               )
    
    done_percentage = fields.Text(
                                  compute="_compute_percentage",
                                  store=True
                                  )
    conf_percentage = fields.Float(
                                  string="Min. Percentage",
                                  store=True,
                                  default=50.00
                                  )
    min_margin_amount = fields.Float(
                                    currency_field="currency",
                                    string="Min. Revenue margin",
                                    compute="_compute_min_margin",
                                    store=True,
                                    readonly=True
                                    )
    objective_type = fields.Selection([
                               ('employee', 'For Employee'),
                               ('panel', 'Panel'),
                               ],
                               index=True,
                               required=True,
                               store=True,
                               help="Is this objective meant to be grouped on a panel?"
                               )
    objective_ids = fields.One2many(
        'employee.objective',
        'objective_id',
        string="Associated objectives for this panel",
        store=True,
        readonly=False
        )
    isPanel = fields.Boolean(
        string="Is panel?",
        readonly=True,
        default=True,
        store=True,
        compute='_compute_is_panel'
        )

    @api.depends('name')
    def _compute_objective_id(self):
        for obj in self:
            #pdb.set_trace()
            obj.objective_id = str(obj.name+'_'+obj.objective_type+'_'+obj.date_open.strftime("%m/%d/%Y"))
            _logger.info('computing ! %s ',obj.objective_id)

    @api.onchange('date_open','date_closed')
    def onchange_end_date( self ):
        if (self.date_open and self.date_closed) and (self.date_open > self.date_closed):
            self.date_closed = self.date_open
            _logger.info('CAMBIANDO FECHAS')
            _logger.info('DC : %s',self.date_closed)
            #raise ValidationError(_('The start date must be less than to the end date.'))

    @api.depends('monetary_objective','conf_percentage')
    def _compute_min_margin(self):
        for obj in self:
            obj.min_margin_amount = obj.conf_percentage*0.01*obj.monetary_objective 
            # valor en $ minimo de ventas

    @api.depends('monetary_objective','actual_revenue')
    def _compute_objective_state(self):
        for obj in self:
            if obj.actual_revenue >= obj.monetary_objective:
                obj.objective_state = True

    @api.depends('actual_revenue','monetary_objective')
    def _compute_percentage(self):
        for obj in self:
            obj.done_percentage = str(round((obj.actual_revenue * 100)/(obj.monetary_objective or 1),2))+"%"

    @api.depends('period','date_open','date_closed')
    def _compute_deadline(self): 
        for obj in self:
            date_beg = obj.date_open
            if obj.period == 'day':
                obj.day_close = 1
                obj.date_closed = obj.date_open + timedelta(days=1)
            if obj.period == 'week':
                obj.day_close = abs((datetime.datetime.now() - (date_beg + timedelta(days=7))).days)
                obj.date_closed = obj.date_open + timedelta(days=7)
            if obj.period == 'fortnight':
                obj.day_close = abs((datetime.datetime.now() -(date_beg + timedelta(days=15))).days)
                obj.date_closed = obj.date_open + timedelta(days=15)
            if obj.period == 'month':
                obj.day_close =abs((datetime.datetime.now() -(date_beg + timedelta(weeks=4))).days)
                obj.date_closed = obj.date_open + timedelta(weeks=4)
            if obj.period == 'trim':
                obj.day_close =abs((datetime.datetime.now() -(date_beg + timedelta(weeks=12))).days)
                obj.date_closed = obj.date_open + timedelta(weeks=12)
            if obj.period == 'quad':
                obj.day_close =abs((datetime.datetime.now() -(date_beg + timedelta(weeks=16))).days)
                obj.date_closed = obj.date_open + timedelta(weeks=16)
            if obj.period == 'year':
                obj.day_close =abs((datetime.datetime.now() -(date_beg + timedelta(days=365))).days)
                obj.date_closed = obj.date_open + timedelta(days=365)

    @api.depends('objective_type')
    def _compute_is_panel(self):
        for pan in self:
            if pan.objective_type == 'employee':
                pan.isPanel = False
            if pan.objective_type == 'panel':
                pan.isPanel = True

    @api.depends('objective_ids','objective_type')
    def _compute_monetary_obj(self):
        for pan in self:
            _monetary_objective = 0
            for obj in pan.objective_ids:
                _monetary_objective += obj.monetary_objective
            pan.monetary_objective = _monetary_objective

    @api.onchange('monetary_objective')
    @api.depends('monetary_objective','type','objective_type','objective_ids')
    def _compute_planned_revenue(self):
        for obj in self:
            _logger.info('%s YIPO TIPO',obj.objective_type)
            if obj.objective_type == 'employee':
                orders_data = self.env['sale.order']
                orders_data = orders_data.search([
                                                  ('user_id', '=', obj.employee_id.user_id.id),
                                                  ('state','in',['sale','done']),
                                                  ('date_order','>=',obj.date_open),
                                                  ('date_order','<=',obj.date_closed)
                                                  ])
                _logger.info('computed _ EMPLOYEE OBJ _____ %s',orders_data)
                for so in orders_data:
                    if obj.type == 'so' and (so.state=='sale' or so.state=='done'):
                        obj.actual_revenue += so.amount_total
                    #_logger.info('Sale orders at : %s',self.id)                    
                    if obj.type == 'inv':
                        #_logger.info('Invoicing at : %s',self.id)
                        for inv in orders_data:
                            if inv.invoice_ids.type == 'out_invoice':
                                obj.actual_revenue += inv.amount_total    
                    if obj.type == 'marg':
                        _logger.info('Revenue margin at : %s',obj.id)
                    obj.actual_revenue += so.margin_extra_cost
            
            if obj.objective_type == 'panel':
                _monetary_objective = 0
                _actual_revenue = 0
                _state = True
                _done_percentage = 0

                for obj_r in obj.objective_ids:
                    #pdb.set_trace()
                    #if (obj_r.type in _type):   #Don't compare apples with oranges
                    _monetary_objective += obj_r.monetary_objective
                    _actual_revenue += obj_r.actual_revenue
                    _state = _state and obj_r.objective_state
                    #IF at least one of the objectives_state is false, then this panel
                    #state, is also false.
                #_done_percentage = round((_actual_revenue * 100)/(_monetary_objective or 1),2)
                obj.monetary_objective = _monetary_objective
                obj.actual_revenue = _actual_revenue
                obj.objective_state = _state
                #obj.done_percentage = _done_percentage
                obj.done_percentage = obj._compute_percentage()
                _logger.info('CONTROL TEST DATA : ______ %s , %s , %s , %s %',obj.monetary_objective,obj.actual_revenue,obj.objective_state,obj.done_percentage)

    
