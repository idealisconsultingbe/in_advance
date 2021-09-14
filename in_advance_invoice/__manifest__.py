# -*- coding: utf-8 -*-
{
    'name': 'In Advance invoice',
    'version': '1.0',
    'summary': '',
    'description': """
      In Advance invoice 
    """,
    'author': 'Idealis Consulting',
    'depends': ['base', 'account', 'approvals'],
    'data': [
        'data/new_approval_type_data.xml',
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/account_move_view.xml',
        'views/approval_request_view.xml',
        'reports/custom_header_invoice.xml',
        'reports/custom_footer_invoice.xml',
        'reports/custom_report_invoice.xml'

    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
