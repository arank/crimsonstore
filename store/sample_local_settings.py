# Django settings for store project.
import os

DEBUG = True

ADMINS = (
    # ('Name', 'email@college.harvard.edu'),
)

INTERNAL_IPS = ('127.0.0.1',)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'crimsononline'
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = '=uva65a*qi9db0n)vkuqgos7w#^xcu&vtngnc8+vfj*xgx=y)%'

# keep this for local dev servers
URL_BASE = 'http://localhost/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
root = os.path.dirname(os.path.realpath(__file__))
MEDIA_ROOT = root + '/../media/' 

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = root + '/../static/'

STATIC_URL = '/static/'

GOOGLE_API_KEY = "ABQIAAAAdoBgu2mGyHlwNmFWklwtOBSMTarlKQyRRh5ucdthk06p19vF5xQFCzYsXKd1Wl-sgDQvPuCHDW3o8A"
