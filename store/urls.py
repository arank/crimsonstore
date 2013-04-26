from django.conf.urls import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from webstore.views import PaypalIPN

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# admin and direct to template URLs
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'store.views.home', name='home'),
    # url(r'^store/', include('store.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
   url(r'^admin/', include(admin.site.urls)),
   url(r'^$', direct_to_template, {'template': 'index.html'})
)

# webstore.views URLs
urlpatterns += patterns('webstore.views',
   url(r'^products/$', 'ProductsAll'),
   url(r'^products/(?P<productslug>.*)/$', 'SpecificProduct'),
   url(r'^events/$', 'EventsAll'),
   url(r'^events/(?P<categoryslug>.*)/$', 'Category'),
   url(r'^singleevent/(?P<eventslug>.*)/$', 'SpecificEvent'),
   url(r'^cart/$', 'Cart'),
   url(r'^search/$', 'Search'),
   url(r'^checkout-success/$', 'Success', name='success'),
   url(r'^checkout-cancel/$', 'Cancel', name='cancel'),
)

# static media and file URLs
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + staticfiles_urlpatterns()

# url for PayPal
(r'^cr!ms0n/p4yp5l/E2E7135958416E4B12258FD3641FD/OwEv0w0ZVt', PaypalIPN())