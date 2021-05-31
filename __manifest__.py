{
    'name': "Letters",

    'summary': """ letter module """,
    
    'description': """
    """,

    'author': "Kenevist",
    'website': "https://kenevist.ir",

    'category': 'Business',
    'application': 'True',
    'version': "14.0.1.0.0",

    'depends': ['base', 'mail', 'user_signature'],
    'data': [
        'security/letter_out_security.xml',
        'security/letter_in_security.xml',
        'security/ir.model.access.csv',
        'data/data_letter.xml',
        'data/letter_content.xml',
        'reports/report_letter_view.xml',
        'views/letter.xml',
        'views/letter_out.xml',
        'views/template_view.xml',
        'views/letter_in.xml',
        'wizard/wizard_views.xml',
    ],

    'css': ['static/src/css/style_report.css'],

    'demo': [
    ],
}