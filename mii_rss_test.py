import unittest

from mii_rss import match


class TestRSS(unittest.TestCase):
    def test_match(self):
        entry = {
            'title': 'homeland s04e09 theres something else going on 1080i hdtv dd5 1 mpeg2-topkek  [no rar]'
        }
        filters = {
            '^homeland.*720p',
            '^star.wars.rebels.*720p',
        }

        self.assertFalse(match(entry, filters))

        entry = {
            'title': 'homeland s04e09 theres something else going on 720p hdtv dd5 1 mpeg2-topkek  [no rar]'
        }

        self.assertTrue(match(entry, filters))
