# -*- coding: utf-8 -*-
"""
General purpose utilities.
"""

import unicodedata
import datetime
import re
from logging import getLogger
from django.forms.models import model_to_dict
import json
import yaml
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from functools import wraps
from random import random
from time import sleep

LOGGER = getLogger(__name__)


def remove_accents(input_str):
    """
    Function to convert accented characters to ASCII, this is useful for things like filenames
    where the underlying system might not support Unicode.

    Copied from
    https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
    """
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def safe_filename(filename):
    """
    Turn a string into a filename we can safely use (and is reasonably readable)
    """
    # First fix any accents
    filename = remove_accents(filename)
    # Then keep only a small set of characters
    return re.sub(r'[^\w\d\.-]', '_', filename)


def parse_boolean(s):
    """
    Parse a boolean from a string
    """
    return s and str(s).lower() not in ('no', 'false', '0')


ISO_8601_RE = re.compile(r'\d+')


def parse_iso8601(s, blank_value=None):
    """
    Quick and dirty parser for ISO8601-like dates.  This is very loose -- it just looks for
    numbers separated by any non-number characters and treats them as datetime inputs.
    eg. '2013-04-15T08:24:12' is the same as '2013x04lots.of.junk15-08/24 12'

    @param blank_value: if blank, return this value (or raise if it's an Exception)
    """
    if not s:
        if isinstance(blank_value, type) and issubclass(blank_value, Exception):
            raise blank_value
        else:
            return blank_value
    try:
        return datetime.datetime(*list(map(int, re.findall(ISO_8601_RE, s))))
    except Exception as e:
        LOGGER.error("Failed to parse iso8601 date %s: %s", s, e)


def to_iso8601(t, with_time=True, separator='T', blank_value=''):
    """
    ISO8601-like datetime formatter

    This is customized due to issues with 2 standard approaches:
    - `t.isoformat()` will omit time info for dates, and will include microseconds if they exist
    - `t.strftime()` will raise an error if the year is <1900

    @param with_time: pass False to return date only
    @param separator: character separating date and time ('T' or ' ' are valid)
    @param blank_value: if blank date given, return a value (or throw if this is an Exception class)
    """
    # If given a string, try to parse it first
    if isinstance(t, (str, bytes)):
        t = parse_iso8601(t)
    # Handle blank value
    if not t:
        if isinstance(blank_value, type) and issubclass(blank_value, Exception):
            raise blank_value
        else:
            return blank_value
    # Ensure we have a datetime rather than just a date
    if not isinstance(t, datetime.datetime):
        t = datetime.datetime.combine(t, datetime.time())
    # Manually format as ISO
    if with_time:
        return '%d-%02d-%02d%s%02d:%02d:%02d' % (
            t.year, t.month, t.day, separator, t.hour, t.minute, t.second
        )
    else:
        return '%d-%02d-%02d' % (t.year, t.month, t.day)


def to_iso8601_date(t, **kwargs):
    """
    Returns a iso8601 date only
    """
    return to_iso8601(t, with_time=False, **kwargs)


def parsetimedelta(s):
    """
    Simple function to turn a string like "2d1h" into a timedelta object

    >>> parsetimedelta('7d')
    datetime.timedelta(7)

    >>> parsetimedelta('7d13h30m16s')
    datetime.timedelta(7, 48616)
    """
    pattern = r'(\d+)(\S)'
    units = {
        'd': 'days',
        'h': 'hours',
        'm': 'minutes',
        's': 'seconds',
    }
    parts = {}
    for value, unit in re.findall(pattern, s):
        if unit not in units:
            raise ValueError("Unknown unit %s in %s" % (unit, s))
        parts[units[unit]] = int(value)
    return datetime.timedelta(**parts)


def make_full_url(url_path):
    """ Prepend the protocol/domain to a URL path (eg from urlresolvers.reverse() """
    # Use https in production only
    if settings.USE_HTTPS_LINKS:
        protocol = 'https'
    else:
        protocol = 'http'
    if url_path.startswith('/'):
        try:
            from django.contrib.sites.models import Site
            return "%s://%s%s" % (
                protocol,
                Site.objects.get_current().domain,
                url_path
            )
        except ImportError:
            LOGGER.error("Failed to import Site")
            return url_path
    else:
        return url_path


def safe_json(obj, **kwargs):
    """ Wrapper to encode JSON using Django's encoder, which safely handles datetime, Decimal, etc. """
    if 'cls' not in kwargs:
        kwargs['cls'] = DjangoJSONEncoder
    return json.dumps(obj, **kwargs)


def parse_json(s, **kwargs):
    """ Wrapper to read JSON, stubbed for now """
    return json.loads(s, **kwargs)


def safe_yaml(obj):
    """
    Return a safe YAML string
    """
    return yaml.dump(obj)


def get_instance_data(instance):
    """
    Return model instance data as a dict (eg. for versioning)
    """
    return model_to_dict(instance)


class RetryableError(Exception):
    """
    Simple wrapper to indicate a retryable exception for @retry
    """
    def __init__(self, cause):
        self.cause = cause


def retry_function(func, count=3, delay=5, backoff=2, jitter=.1, exc_types=RetryableError):
    """
    Return a function that will run the given function, retrying on errors

    @param count: how many times to try
    @param delay: base delay for retry (in seconds)
    @param backoff: factor for increasing delay on each subsequent retry (eg. 2 = wait twice as long each time)
    @param jitter: randomize the delay by this factor
    @param exc_types: types of exceptions to retry
    """
    @wraps(func)
    def result(*args, **kwargs):
        last_exc = None
        next_delay = delay
        for _ in range(count):
            # Delay if we are retrying
            if last_exc and next_delay:
                # Add jitter to the actual delay, since this is sometimes a concurrency
                # issue we want to avoid having separate threads run in lockstep
                actual_delay = int(next_delay * (1 + jitter * (random() * 2 - 1)))
                LOGGER.warning("Retrying in %s (actually %s) seconds", next_delay, actual_delay)
                sleep(actual_delay)
                next_delay = next_delay * backoff
            try:
                return func(*args, **kwargs)
            except exc_types as e:
                LOGGER.error("Retryable error: %s", e)
                last_exc = e
                pass
            except Exception as e2:
                LOGGER.error("Unretryable error: %s", e2)
                raise
        if hasattr(last_exc, 'cause'):
            raise last_exc.cause
        else:
            raise last_exc
    return result


def retry(*args, **kwargs):
    """
    Decorator that will cause a function to be retried if it throws a particular exception

    @param count: how many times to try
    @param delay: base delay for retry (in seconds)
    @param backoff: factor for increasing delay on each subsequent retry (eg. 2 = wait twice as long each time)
    @param jitter: randomize the delay by this factor
    @param exc_types: types of exceptions to retry
    """
    def decorator(func):
        return retry_function(func, *args, **kwargs)
    return decorator


class _FormatSafe(object):
    """
    Something to return for .format() that won't blow up if you breathe on it wrong
    """
    def __init__(self, **wraps):
        self.wraps = wraps

    def __len__(self):
        return len(self.wraps)

    def __repr__(self):
        return repr(self.wraps)

    def __getitem__(self, attr):
        return self.wraps.get(attr, '')


def safe_format(**kwargs):
    return _FormatSafe(**kwargs)


def display_formataddr(addr, parens=True):
    """
    Display-oriented version of email.formataddr.

    This should just return a "name <email>" string suitable for display (ie. in UTF8)

    If `parens` is True, use '()' rather than '<>' around the email
    """
    brackets = '()' if parens else '<>'
    try:
        (name, email) = addr
        if name:
            return '%s %s%s%s' % (name, brackets[0], email, brackets[1])
        else:
            return email
    except Exception as e:
        LOGGER.error("Failed to format address %s : %s", addr, e)
        return ''
