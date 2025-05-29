"""
WSGI config for collectible_catalog project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collectible_catalog.settings')

application = get_wsgi_application()