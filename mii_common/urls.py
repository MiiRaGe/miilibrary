from django.urls import include, re_path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

from mii_indexer import views as mii_indexer_views
from mii_interface import views as mii_interface_views
from mii_rss import views as mii_rss_views
from mii_sorter import views as mii_sorter_views
from mii_unpacker import views as mii_unpacker_views

admin.autodiscover()

urlpatterns = [
    re_path(r'^$', mii_interface_views.index, name='home'),
    re_path(r'^movies$', mii_interface_views.movies, name='movies'),
    re_path(r'^series$', mii_interface_views.series, name='series'),
    re_path(r'^rate$', mii_interface_views.rate, name='rate'),
    re_path(r'^discrepancies', mii_interface_views.discrepancies, name='discrepancies'),
    re_path(r'^reports$', mii_interface_views.reports, name='reports'),
    re_path(r'^report/(?P<report_id>[0-9]+)/$', mii_interface_views.report, name='report'),
    re_path(r'^play', mii_interface_views.play, name='play'),
    re_path(r'^rpc/index$', mii_indexer_views.start_index, name='start_index'),
    re_path(r'^rpc/apply_index', mii_indexer_views.start_apply_index, name='apply_index'),
    re_path(r'^rpc/sort$', mii_sorter_views.start_sort, name='start_sort'),
    re_path(r'^rpc/unpack$', mii_unpacker_views.start_unpacker, name='start_unpacker'),
    re_path(r'^rpc/rss', mii_rss_views.check_feeds, name='check_feeds'),
    re_path(r'^rpc/recheck_rss', mii_rss_views.recheck_feeds, name='recheck_feeds'),
    re_path(r'^rpc/unpack_sort_index', mii_interface_views.start_unpack_sort_indexer, name='unpack_sort_index'),
    re_path(r'^admin/', admin.site.urls),
]