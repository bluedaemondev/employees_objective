# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'employee_objective',
    'version': '1.0',
    'category': 'Sales',
    'sequence': 5,
    'summary': 'Track employee-s sale/leads/invoicing individual objectives.',
    'description': "",
    'website': '',
    'depends': [
        'sale',
        'hr',
	'web',
	'web_kanban_gauge',
    ],
    'data': [
    	'security/ir.model.access.csv',
    	'security/objective_gauges_security.xml',
        'views/control_objective_user.xml',
        'views/sales_panel.xml',
        #'views/employee_objective_panel_views.xml',
    ],
    'demo': [
    ],
    #'css': ['static/src/css/crm.css'],
    'installable': True,
    'application': True,
    'auto_install': False,
    #'uninstall_hook': 'uninstall_hook',
}
