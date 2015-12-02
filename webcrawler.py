__author__ = 'christopherlyver'
import socket
import urlparse
import urllib
import re

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

# If we receive a sessionId, hold onto it
session_id = None

# If we find a flag, we'll keep it here
found_flags = []

# HTTP encoding for newline
crlf = "\r\n\r\n"

username = '001180021'
passwd = 'E1ELONFK'


def get(url):
    """
    Make a GET request to the given url
    """

    parsed_url = urlparse.urlparse(url)
    path = parsed_url.path
    if not path:
        path = "/"

    # Fire away
    sock.send("GET {} HTTP/1.0{}".format(path, crlf))
    data = sock.recv(1000000)
    return repr(data)


def post(url, params):
    """
    Make a POST request to the given url, needed for authentication.
    """
    parsed_url = urlparse.urlparse(url)
    path = parsed_url.path
    if not path:
        path = '/'

    #print url
    #print path
    params = urllib.urlencode(params)
    message = "POST {} HTTP/1.0{}".format(path, crlf)
    content_len = "Content-Length: {}{}".format(len(params), crlf)
    host = "Host: fring.ccs.neu.edu{}".format(crlf)
    user_agent = "User-Agent: Mozilla/5.0" + crlf
    accept = "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n" + crlf
    content_type = "Content-Type: application/x-www-form-urlencoded{}".format(crlf)
    form_cookie = "Cookie: csrftoken={}; sessionid={}{}".format(cookie, session_id, crlf)
    accept_laguage = "Accept-Language: en-us,en;q=0.5" + crlf
    keep_alive = "Connection: keep-alive" + crlf

    message = message + content_len + content_type + form_cookie + host + user_agent + accept + accept_laguage + keep_alive + params + crlf

    print message

    sock.send(message)

    print sock.recv(1000000)


def open_socket():
    """
    Establish and return a tcp socket
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return s


def connect_socket(s, address, port):
    """
    Return a socket that is connected to the given address/port
    """
    s.connect((address, port))
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
    # A url is in our target domain if the target domain is in the url, and the first most element
    return target_domain in url and not url.split(target_domain)[0]


def print_flags():
    """
    Print all flags found so far.
    """
    if found_flags:
        for flag in found_flags:
            print flag
    else:
        print "No flags found"


def get_cookies():
    """
    Establish the csrf cookie and session id, provided before authentication
    """
    global cookie, session_id
    login_page_html = get(target_login)
    cookie_jar = fetch_patterns(r"Set-Cookie\:(?:(?!;)(?:.|\n))*;", login_page_html)
    cookie = cookie_jar[0].split('=')[1].split(';')[0]
    session_id = cookie_jar[1].split('=')[1].split(';')[0]
    return cookie, session_id


def login():
    csrf_cookie, session_id = get_cookies()
    params = {'username': username,
              'password': passwd,
              'csrfmiddlewaretoken': csrf_cookie,
              'next': '/fakebook/'}
    post(target_login, params)

# We need one connection
# Establish and connect our socket
sock = open_socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host_ip = socket.gethostbyname('fring.ccs.neu.edu')
sock = connect_socket(sock, host_ip, 80)

login()
# Close up shop...
sock.shutdown(1)
sock.close()


