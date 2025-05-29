"""
ASGI config for collectible_catalog project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collectible_catalog.settings')

application = get_asgi_application()