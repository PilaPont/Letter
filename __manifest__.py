{
    'name': "Letters",
    'version': '14.0.0.2.0.0+210615',
    'description': """
    A module to handle all sent and received letters, parcels, goods, catalogues and etc. in a company
    """,
    'category': 'Marketing',
    'author': "Kenevist, Maryam Kia, PmN",
    'website': "https://kenevist.ir",

    'depends': ['report_core', 'mail', 'user_signature', 'calendar'],
    'data': [
        'security/letter_security.xml',
        'security/letter_layout_security.xml',
        'security/ir.model.access.csv',
        'data/data_letter.xml',
        'data/letter_content.xml',
        'reports/letter_templates.xml',
        'reports/letter_reports.xml',
        'views/letter_views.xml',
        'views/letter_layout_views.xml',
        'wizard/wizard_views.xml',
    ],

    'application': 'True',
}