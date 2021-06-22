{
    'name': "Letters",
    'version': '14.0.0.2.0.0+210615',
    'description': """
    A module to handle all sent and received letters, parcels, goods, catalogues and etc. in a company
    """,
    'category': 'Marketing',
    'author': "Kenevist, Maryam Kia",
    'website': "https://kenevist.ir",

    'depends': ['base', 'mail', 'user_signature'],
    'data': [
        'security/letter_security.xml',
        'security/template_security.xml',
        'security/ir.model.access.csv',
        'data/data_letter.xml',
        'data/letter_content.xml',
        'reports/report_letter_view.xml',
        'views/letter_views.xml',
        'views/letter_header_views.xml',
        'wizard/wizard_views.xml',
    ],

    'application': 'True',
}