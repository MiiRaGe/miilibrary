from django.http import HttpResponse

from mii_sorter.tasks import sort


def start_sort(request):
    sort.delay()
    return HttpResponse()