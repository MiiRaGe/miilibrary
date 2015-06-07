from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse

urlpatterns = patterns('',
                       url(r'^rpc/unpack$', 'mii_unpacker.views.start_unpacker', name='start_unpacker'),
)
