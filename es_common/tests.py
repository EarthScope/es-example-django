from django.test import TestCase
from es_common.data_id import join_provenances, create_data_id
from es_common.templatetags.es_common_tags import as_timedelta
import datetime
from django.core.validators import URLValidator



class DataIdentifierTest(TestCase):

    def validate_url(self, url):
        try:
            URLValidator()(url)
        except Exception as e:
            self.fail("Invalid URL: %s" % url)

    def test_create_data_id_1(self):
        """
        Basic test for data id creation
        """
        self.validate_url(create_data_id("example"))


class DataProvenanceTest(TestCase):
    def test_join_provenances_1(self):
        """
        Test the logic for joining
        """
        provenance1 = ['a', 'b', 'c', 'd']
        provenance2 = ['a', 'c', 'c2', 'd']
        joined = join_provenances(provenance1, provenance2)
        self.assertEqual(
            joined,
            ['a', 'b', 'c', 'd', 'c2'],
        )


class AsTimedeltaFilterTest(TestCase):
    def test_as_timedelta1(self):
        self.assertEqual(
            as_timedelta(datetime.timedelta(days=3, hours=4, minutes=2)),
            '3d:4h'
        )
        self.assertEqual(
            as_timedelta(datetime.timedelta(hours=4, minutes=2, seconds=30)),
            '4h:2m'
        )
        self.assertEqual(
            as_timedelta(datetime.timedelta(seconds=30, milliseconds=234)),
            '30s'
        )
        self.assertEqual(
            as_timedelta(datetime.timedelta(seconds=3, milliseconds=234)),
            '3.23s'
        )
        self.assertEqual(
            as_timedelta(datetime.timedelta(microseconds=87236)),
            '87.2ms'
        )
