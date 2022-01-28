# -*- coding: utf-8 -*-
{
    'name': "Laundry Management",
    'summary': """Put on wings to your Laundry Business""",
    'description': """
        This app will manage the laundry and their works, And Put on wings to your Laundry Business.
    """,
    'author': 'ErpMstar Solutions',
    'category': 'Sales',
    'version': '1.2',
    'depends': ['sale'],
    # always loaded
    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'wizards/return_wizard.xml',
        'reports/laundry_report.xml',
        'reports/tracking_code_tag.xml',

    ],
    'images': [
        'static/description/main.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 70,
    'currency': 'EUR',
}
