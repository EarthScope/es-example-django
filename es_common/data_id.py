"""
Example / testbed for Data Identifier usage
"""
import uuid
from es_common.utils import to_iso8601, to_iso8601_date
import datetime
from urllib.parse import urlencode


def create_data_id(datatype, paths=None, add_date=False, add_datetime=False, add_uuid=True, qs=None):
    """
    Top-level interface for creating a data id

    >>> create_data_id('mydata', paths=['one', 'two'], add_date=True, add_uuid=True)
    "http://earthscope.org/mydata/one/two/2021-01-01/11230sx-a22g-2721-a0234adba/"

    @param paths {list} path-like elements for the id (ie. data hierarchy)
    @param add_date {bool} add a path element with the current date
    @param add_datetime {bool} add a path element with the current datetime
    @param add_uuid {bool} add a path element with a UUID
    @param qs {object} append a query string
    """
    # Need data or added uuid
    fullpath = [
        datatype,
    ]
    if paths:
        fullpath.extend(list(str(p) for p in paths))
    if add_datetime:
        fullpath.append(to_iso8601(datetime.datetime.now()))
    elif add_date:
        fullpath.append(to_iso8601_date(datetime.date.today()))
    if add_uuid:
        fullpath.append(str(uuid.uuid1()))

    return "http://earthscope.org/%s/%s" % (
        "/".join(fullpath),
        ("?%s" % urlencode(qs)) if qs else '',
    )

def join_provenances(provenance1, provenance2):
    """
    Given two provenances (lists of id strings) join them together
    """
    # Use a dict to join them
    joined = dict(
        (p, True) for p in provenance1
    )
    joined.update(
        (p, True) for p in provenance2
    )
    return list(joined.keys())
