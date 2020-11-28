# -*- coding: utf-8 -*-
{
    'name': "Letters",

    'summary': """ letter module """,
    
    'description': """
        Long description of module's purpose
    """,

    'author': "Assan Ideh",
    'website': "http://www.assanidea.com",

    'category': 'Business',
    'application': 'True',
    'version': '0.1',
    'depends': ['base', 'mail', 'access_group'],
    'data': [
        'views/letter_template.xml',
        'security/letter_out_security.xml',
        'security/letter_in_security.xml',
        'security/ir.model.access.csv',
        'data/data_letter.xml',
        'reports/report_letter_view.xml',
        'views/letter.xml',
        'views/letter_out.xml',
        'views/template_view.xml',
        'views/letter_in.xml',
        'wizard/wizard_views.xml',
    ],

    'css': ['static/src/css/style_report.css'],

    'demo': [
        'demo/demo.xml',
    ],
}