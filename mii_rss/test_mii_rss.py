from django.test import TestCase

from tasks import match


class TestRSS(TestCase):
    def test_match(self):
        entry = {
            'title': 'homeland s04e09 theres something else going on 1080i hdtv dd5 1 mpeg2-topkek  [no rar]'
        }
        filters = {
            '^homeland.*720p',
            '^star.wars.rebels.*720p',
            '^better.call.saul.*720p'
        }

        self.assertFalse(match(entry, filters)[0])

        entry = {
            'title': 'homeland s04e09 theres something else going on 720p hdtv dd5 1 mpeg2-topkek  [no rar]'
        }

        self.assertTrue(match(entry, filters)[0])

        entry = {
            'title': 'better call saul s01e01 720p hdtv x264-killers [no rar]'
        }
        self.assertTrue(match(entry, filters)[0])
