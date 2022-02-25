{
    'name': "Online Reservation System",
    'version': "1.0.2",
    'author': "SMART",
    'category': "Tools",
    'summary': "Allow website users to book reservation from the website",
    'license':'LGPL-3',
    'data': [
        'data/data.xml',
        'views/website_calendar_views.xml',
        'views/website_calendar_booking_templates.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['website', 'calendar'],
    'images':[
        'static/description/1.jpg',
        'static/description/2.jpg',
        'static/description/3.jpg',
    ],
    'installable': True,
    'qweb': ['static/src/xml/*.xml'],
}