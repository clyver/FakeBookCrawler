#!/usr/bin/python
__author__ = 'christopherlyver'
import socket
import urlparse
import re
from copy import copy
import sys

# FakeBook crawler, implemented through raw sockets #

# Standard http port
http_port = 80
# The target host
target_host = 'fring.ccs.neu.edu'
# The root url *Not publically routable*
target_domain = 'http://fring.ccs.neu.edu/fakebook/'
# The login url
target_login = 'http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/'

# Site paths observed, but not yet visited
frontier = set()
# Site paths visited, needed to prevent looping
visited = set()
# Keep any authentication tokens here
cookie_jar = {}

# If we find a flag, we'll keep it here
found_flags = []

# HTTP encoding for newline
eol = "\r\n"
crlf = "\r\n\r\n"

cl_args = sys.argv
username = cl_args[1]
password = cl_args[2]


def get(url):
    """
    Make a GET request to the given url
    """
    global cookie_jar
    # Open a socket to do our dirty business
    sock = open_socket()

    # We'll need to know what path to request
    parsed_url = urlparse.urlparse(url)
    path = parsed_url.path
    if not path:
        path = "/"

    # Format our request
    get_request = "GET {} HTTP/1.1{}".format(path, eol) + \
                  "Host:fring.ccs.neu.edu{}".format(eol) + \
                  "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:39.0) Gecko/20100101 Firefox/39.0{}".format(eol)+ \
                  "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8{}".format(eol)+ \
                  "Accept-Language: en-US,en;q=0.5{}".format(eol)+ \
                  "Connection:keep-alive{}".format(eol)+ \
                  "Content-Type: application/x-www-form-urlencoded{}".format(eol)
    if cookie_jar:
        # Include the freshest, hot-out-the-oven cookies
        csrf_token = cookie_jar.get('csrf_token')
        session_id = cookie_jar.get('session_id')
        get_request += "Cookie:csrftoken="+csrf_token+"; sessionid="+session_id+"\r\n"

    # Add a happy little line break, our little secret
    get_request += crlf

    # Fire away, and close up shop
    sock.send(get_request)
    data = sock.recv(4096)
    sock.close()
    return data


def post():
    """
    Make a POST request to the given url, hardcoded for FakeBook authentication.
    """
    global cookie_jar, username, password
    # Get the ball rolling with a connected socket
    sock = open_socket()

    # Pull the latest cookies
    csrf_token = cookie_jar.get('csrf_token')
    sess_id = cookie_jar.get('session_id')

    body = "csrfmiddlewaretoken={}".format(csrf_token) + \
           "&username={}".format(username) + \
           "&password={}".format(password) + \
           "&next=%2Ffakebook%2F{}".format(crlf)
    body_len = len(body)
    headers = "POST /accounts/login/ HTTP/1.1{}".format(eol)+ \
              "Host:fring.ccs.neu.edu{}".format(eol)+ \
              "Referer: http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/{}".format(eol) + \
              "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5)" + \
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36{}".format(eol)+ \
              "Cookie:csrftoken={}; sessionid={}{}".format(csrf_token, sess_id, eol) + \
              "Connection:keep-alive{}".format(eol) + \
              "Content-Type: application/x-www-form-urlencoded{}".format(eol) + \
              "Content-Length:{}{}".format(body_len, crlf)

    post_request = headers + body
    sock.sendall(post_request)
    response = sock.recv(4096)
    sock.close()
    return response


def open_socket():
    """
    Establish and return a tcp socket connected to the target host
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((target_host, http_port))
    return s


def fetch_patterns(regex, html):
    """
    Give some regular expression and html, return a list of pattern matches
    """
    # My regexFoo needs work, but this will do... for now
    # Our flags will be sandwiched between 'FLAG:' and '</h2>'
    pattern_matches = re.findall(regex, html)
    return pattern_matches


def parse_flag(pattern):
    """
    Takes a matched pattern from fetch_flags() and returns
    the actual flag
    """
    splice1 = pattern.split(':')[1]
    flag = splice1.split('<')[0]
    return flag


def fetch_flag_patterns(html):
    """
    Give some html, use regular expressions to find secret flags.
    We anticipate all flags to be sandwiched between: 'FLAG:' and '</h2>'
    """
    # My regexFoo needs work, but this will do... for now
    # Our flags will be sandwiched between 'FLAG:' and '</h2>'
    pattern_matches = fetch_patterns(r"FLAG\:(?:(?!</h2>)(?:.|\n))*</h2>", html)
    return pattern_matches


def fetch_flags(html):
    """
    Given some html, return True if flags are present, else False.
    If secret flags are found, they will be appended to the global found_flags list
    """
    global found_flags
    pattern_matches = fetch_flag_patterns(html)
    if pattern_matches:
        # For all matches, do the necessary splicing, and append to found_flags
        for pattern in pattern_matches:
            flag = parse_flag(pattern)
            found_flags.append(flag)
        return True
    else:
        return False


def is_valid_url(url):
    """
    Return True if the url is within the target domain.
    We don't want to crawl over sites outside of our intended scope.
    """
    # A url is in our target domain if the target domain if preceded with /fakebook/
    return not url.split('fakebook/')[0]


def fetch_urls(html):
    """
    Given some html, return a list of valid links not yet visited
    """

    p = re.compile(ur'fakebook(?:(?!>)(?:.|\n))*/')
    all_urls = fetch_patterns(p, html)
    return [url for url in all_urls if (is_valid_url(url)) and url not in visited]


def print_flags():
    """
    Print all flags found so far.
    """
    if found_flags:
        for flag in found_flags:
            print flag
        return found_flags
    else:
        print "No flags found"
        return []


def get_cookies():
    """
    Establish the csrf cookie and session id, provided before authentication
    """
    global cookie_jar
    login_page_html = get(target_login)
    cookies = fetch_patterns(r"Set-Cookie\:(?:(?!;)(?:.|\n))*;", login_page_html)
    csrf_token = cookies[0].split('=')[1].split(';')[0]
    session_id = cookies[1].split('=')[1].split(';')[0]
    cookie_jar.update({'csrf_token': csrf_token})
    cookie_jar.update({'session_id': session_id})


def crawl():
    global cookie_jar
    # Make a GET to the login page, and get our cookies
    get_cookies()
    # Login and get the response
    login_response = post()
    # The login page returns a new session id that we'll need moving forward
    cookies = fetch_patterns(r"Set-Cookie\:(?:(?!;)(?:.|\n))*;", login_response)
    final_session_id = cookies[0].split('=')[1].split(';')[0]
    cookie_jar['session_id'] = final_session_id


    # Make a GET to the redirected /fakebook/
    initial_page = get(target_domain)

    # Time to add the home page to the list of visited sites
    visited.add('fakebook/')

    # The urls from the initial page:
    initial_urls = fetch_urls(initial_page)
    # Add those initial urls to the frontier
    frontier.update(initial_urls)

    while True:
        # If there's no new links on the frontier, we're done
        if not frontier:
            # FakeBook. The Final frontier.
            break
        # *Caution*: Iterating over list we are mutating
        for link in copy(frontier):
            # First thing's first.  Remove from this link frontier, and add to visited
            frontier.remove(link)
            visited.add(link)

            # GET this page, search for flags.  The concat of / is a hack, we should fix the regex
            page = get('/' + link)
            # Extract any flags on the page
            fetch_flags(page)

            # We need to look on this page for links we haven't been to yet
            frontier.update(fetch_urls(page))

    # Print all found flags
    print_flags()

# Boom goes the dynamite
crawl()
