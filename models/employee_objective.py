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

class PanelObjective(models.Model):

    _name = "panel.objective"

    name = fields.Char(string='Panel Name', required=True)


class EmployeeObjective(models.Model):

    _name = "employee.objective"
    _description = 'employees objective log. Multiple types and periods are stored.'
    _order = "create_date"
    
    panel_id = fields.Many2one(
                                  'panel.objective',
                                  string="Panel",
                                  required=True
                                )
    objective_id = fields.Char(
                                  string="Objective index",
                                  compute=False,
                                  store=True
                                  )
    employee_id = fields.Many2one(
                                  'hr.employee',
                                  string="Employee related to this objective",
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
                        required=True
                        )
    notes = fields.Text(
                        string="Other Info...",
                        )

    currency = fields.Many2one(
                                'res.currency',
                                string='Currency',
                            )
    monetary_objective = fields.Integer(
                                         string="Monetary Objective",
                                         readonly=False,
                                         required=True,
                                         compute=False,
                                         store=True
                                        )  
    actual_revenue = fields.Integer(
                                    compute='_compute_planned_revenue',
                                    inverse="_set_planned_revenue",
                                    readonly=False,
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
                            default='marg',
                            help="Type is used to separate different objectives for employees."
                            )
    objective_state = fields.Selection(
                                    [('draft','Draft'),('confirmed','Confirmed'),('done','Done'),('disabled','Disabled')],
                                    string="Current state",
                                    readonly=False,
                                    default='draft',
                                    store=True,
                                    compute=False
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
                               default='month',
                               help="Assign a period for this objective."
                               )
    done_percentage = fields.Text(
                                  compute="_compute_percentage"
                                  )
    conf_percentage = fields.Float(
                                  string="Min. Percentage",
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
                               ('employee', 'Employee'),
                               ('panel', 'Group'),
                               ],
                               index=True,
                               required=True,
                               default='employee',
                               help="Is this objective meant to be grouped on a panel?"
                               )
    objective_ids = fields.One2many(
        'employee.objective',
        'objective_id',
        string="Associated objectives for this group",
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
            obj.objective_id = str(obj.name+'_'+obj.objective_type+'_'+obj.date_open.strftime("%m/%d/%Y"))
            _logger.info('computing ! %s ',obj.objective_id)

    @api.onchange('date_open','date_closed')
    def onchange_end_date( self ):
        if (self.date_open and self.date_closed) and (self.date_open > self.date_closed):
            self.date_closed = self.date_open
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

    @api.depends('monetary_objective','type','objective_state','objective_ids')
    def _compute_planned_revenue(self):
        for obj in self.sorted(lambda x: x.objective_type == 'panel'):
            #pdb.set_trace()
            _last_val = obj.actual_revenue
            _actual_revenue = 0
            if obj.objective_type == 'employee':
                orders_data = self.env['sale.order']
                orders_data = orders_data.search([
                                                  ('user_id', '=', obj.employee_id.user_id.id),
                                                  ('state','in',['sale','done']),
                                                  ('date_order','>=',obj.date_open),
                                                  ('date_order','<=',obj.date_closed)
                                                  ])
                for so in orders_data:
                    if obj.type == 'so' and (so.state=='sale' or so.state=='done'):
                        obj.actual_revenue += so.amount_total
                    if obj.type == 'inv':
                        for inv in orders_data:
                            if inv.invoice_ids.type == 'out_invoice':
                                obj.actual_revenue += inv.amount_total    
                    if obj.type == 'marg':
                        obj.actual_revenue += so.margin_extra_cost
            else:
                #pdb.set_trace()
                objs_data = self.env['employee.objective']
                objs_data = objs_data.search([
                                                ('panel_id','=',obj.panel_id.id),
                                                ('objective_type','=','employee')
                                                ])
                for item in objs_data:
                    _actual_revenue += item.actual_revenue
                #pdb.set_trace()
                obj.actual_revenue = _actual_revenue

    def _compute_panel(self,state):
        for pan in self:
            if pan.objective_type == 'panel' and pan.isPanel:
                _actual_revenue = 0
                _monetary_objective = 0
                _done_percentage = 0
                for obj_r in pan.objective_ids.filtered(lambda x: x.objective_type != 'panel'):
                    _monetary_objective += obj_r.monetary_objective
                    _actual_revenue += obj_r.actual_revenue
                
                pan.objective_state = state['new_state']
                pan.actual_revenue = _actual_revenue #_set_planned_revenue(_actual_revenue) # = _actual_revenue
                pan.monetary_objective = _monetary_objective
                #pdb.set_trace()
                pan._compute_percentage() # pan.done_percentage = 
    
    def _set_planned_revenue(self,val=False):
        #keep last value from "_compute_panel"
        if self.objective_type == 'panel' and val != False:
            #pdb.set_trace()
            self.actual_revenue = val
    
    def action_change_state(self, ctxt):
        if self.objective_type == 'panel':
            self._compute_panel(ctxt)
