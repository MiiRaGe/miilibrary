from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'mii_interface.views.index', name='home'),
    url(r'movies^$', 'mii_interface.views.movies', name='movies'),
    url(r'series^$', 'mii_interface.views.series', name='series'),
    url(r'^rpc/index$', 'mii_indexer.views.start_index', name='start_index'),
    url(r'^rpc/sort$', 'mii_sorter.views.start_sort', name='start_sort'),
    url(r'^rpc/unpack$', 'mii_unpacker.views.start_unpacker', name='start_unpacker'),
    url(r'^admin/', include(admin.site.urls)),
)
