from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^rpc/index$', 'mii_indexer.views.start_index', name='start_index'),
)
