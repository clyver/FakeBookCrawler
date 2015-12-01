__author__ = 'christopherlyver'
import socket
import urlparse

# FakeBook crawler, implemented through raw sockets #

# The root url
target_domain = 'http://fring.ccs.neu.edu/fakebook/'
# The login url
target_login = 'http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/'

# Site paths observed, but not yet visited
frontier = []
# Site paths visited, needed to prevent looping
visited = []

# If we receive a cookie, hold onto it
cookie = None

# If we find a flag, we'll keep it here
flags = []


def get(url):
    """
    Make a GET request to the given url
    """
    pass


def post(url, credentials):
    """
    Make a POST request to the given url, needed for authentication.
    """
    pass


def fetch_flag(html):
    """
    Given some html, return a flag if it is present, else False.
    """


def is_valid_url(url):
    """
    Return True if the url is within the target domain.
    We don't want to crawl over sites outside of our intended scope.
    """
    pass


def print_flags():
    """
    Print all flags found so far.
    """
    pass

