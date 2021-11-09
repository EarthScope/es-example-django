"""
Utilities for interacting with the vouch-proxy interface

For the most part the django-vouch-proxy-auth middleware 
handles everything, but this library is to provide more
nuts and bolts access
"""
import base64
import gzip
import json
import logging

import jwt
import requests
from django.conf import settings

LOGGER = logging.getLogger(__name__)


class VouchProxyJWT(object):

    cookie_name = 'VouchCookie'
    request = None
    raw_value = None
    errors = None
    value = None

    def __init__(self, request=None, raw_value=None, value=None):
        if request:
            self.from_request(request)
        elif raw_value:
            self.from_raw_value(raw_value)
        elif value:
            self.value = value

    def is_valid(self):
        """
        Is there a valid JWT value?
        """
        return bool(self.value)

    def from_request(self, request):
        """
        Set and parse a request
        """
        self.request = request
        self.from_raw_value(self.get_cookie_jwt(request))

    def from_raw_value(self, raw_value):
        """
        Set and parse the raw cookie value
        """
        self.raw_value = raw_value
        if raw_value:
            self.valid = self.vouch_validate(raw_value)
            # Note we get the value regardless of validity
            self.value = self.get_jwt_payload(raw_value)
    
    def get_cookie_jwt(self, request):
        """
        Get the JWT data from the vouch-proxy cookie
        """    
        return request.COOKIES.get(self.cookie_name)

    def get_jwt_payload(self, raw_value):
        """
        Get the JWT data from a cookie value
        """
        # Vouch cookie is URL-safe Base64 encoded Gzipped data
        decompressed = gzip.decompress(base64.urlsafe_b64decode(raw_value))
        payload = jwt.decode(decompressed, options={'verify_signature': False})
        return payload

    def vouch_validate(self, raw_value):
        """
        Validate a cookie value with the Vouch-Proxy endpoint
        Raises an exception on failure!
        """
        validate = requests.get(
            settings.VOUCH_PROXY_VALIDATE_ENDPOINT,
            cookies={self.cookie_name: raw_value},
            verify=False,
        )
        validate.raise_for_status()

    def get_user_id(self):
        """
        Get the user identifier associated with the login
        """
        pass


