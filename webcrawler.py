__author__ = 'christopherlyver'
import socket
import urlparse
import re
from copy import copy

# FakeBook crawler, implemented through raw sockets #

# Standard http port
http_port = 80
# The target host
target_host = 'fring.ccs.neu.edu'
# The root url
target_domain = 'http://fring.ccs.neu.edu/fakebook/'
# The login url
target_login = 'http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/'

# Site paths observed, but not yet visited
frontier = set()
# Site paths visited, needed to prevent looping
visited = set()

# If we find a flag, we'll keep it here
found_flags = []

# HTTP encoding for newline
crlf = "\r\n\r\n"

username = '001180021'
passwd = 'E1ELONFK'


def get(url, cookies=None, ):
    """
    Make a GET request to the given url
    """
    sock = open_socket()

    parsed_url = urlparse.urlparse(url)
    path = parsed_url.path
    if not path:
        path = "/"

    # Fire away
    get_request = "GET {} HTTP/1.0{}".format(path, crlf)
    if cookies:
        csrf_token = cookies.get('csrf_token')
        sess_id = cookies.get('session_id')

        get_request = "GET {} HTTP/1.0\r\n".format(path) + \
                      "Host:fring.ccs.neu.edu\r\n" + \
                      "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:39.0) Gecko/20100101 Firefox/39.0\r\n" + \
                      "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n" + \
                      "Accept-Language: en-US,en;q=0.5\r\n" + \
                      "Cookie:csrftoken="+csrf_token+"; sessionid="+sess_id+"\r\n" + \
                      "Connection:keep-alive\r\n" + \
                      "Content-Type: application/x-www-form-urlencoded\r\n\r\n"

    sock.send(get_request)
    data = sock.recv(4096)
    sock.close()
    return data


def post(params):
    """
    Make a POST request to the given url, needed for authentication.
    """
    sock = open_socket()

    csrf_token = params.get('csrfmiddlewaretoken')
    sess_id = params.get('sessionid')
    user = params.get('username')
    password = params.get('password')

    http_params = "csrfmiddlewaretoken="+csrf_token+"&username="+user+"&password="+password+"&next=%2Ffakebook%2F"
    params_len = len(http_params)
    final_message = "POST /accounts/login/ HTTP/1.0\r\n" + \
                    "Host:fring.ccs.neu.edu\r\n" + \
                    "Referer: http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/\r\n" + \
                    "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5)" + \
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36\r\n" + \
                    "Cookie:csrftoken="+csrf_token+"; sessionid="+sess_id+"\r\n" + \
                    "Connection:keep-alive\r\n" + \
                    "Content-Type: application/x-www-form-urlencoded\r\n" + \
                    "Content-Length:{}\r\n\r\n".format(params_len) + \
                    http_params + "\r\n\r\n"

    sock.sendall(final_message)
    response = sock.recv(4096)
    sock.close()

    return response


def open_socket():
    """
    Establish and return a tcp socket
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
    global cookie, session_id
    login_page_html = get(target_login)
    cookie_jar = fetch_patterns(r"Set-Cookie\:(?:(?!;)(?:.|\n))*;", login_page_html)
    cookie = cookie_jar[0].split('=')[1].split(';')[0]
    session_id = cookie_jar[1].split('=')[1].split(';')[0]
    return cookie, session_id


def crawl():
     # Make a GET to the login page, and get our cookies
    csrf_cookie, sess_id = get_cookies()
    params = {'username': username,
              'password': passwd,
              'csrfmiddlewaretoken': csrf_cookie,
              'sessionid': session_id,
              'next': '/fakebook/'}
    # Login and get the response
    login_response = post(params)
    # The login page returns a new session id that we'll need moving forward
    cookies = fetch_patterns(r"Set-Cookie\:(?:(?!;)(?:.|\n))*;", login_response)
    final_session_id = cookies[0].split('=')[1].split(';')[0]

    cookie_jar = {'session_id': final_session_id, 'csrf_token': csrf_cookie}
    # Make a GET to the redirected /fakebook/
    initial_page = get(target_domain, cookie_jar)

    # Time to add the home page to the list of visited sites
    visited.add('fakebook/')

    # The urls from the initial page:
    initial_urls = fetch_urls(initial_page)
    # Add those initial urls to the frontier
    frontier.update(initial_urls)

    while True:
        # If there's no new links on the frontier, we're done
        if not frontier:
            break
        for link in copy(frontier):
            # First thing's first.  Remove from frontier, add to visited
            frontier.remove(link)
            visited.add(link)

            # GET this page, search for flags.  The concat of / is a hack, we should fix the regex
            page = get('/' + link, cookie_jar)
            # Extract any flags on the page
            fetch_flags(page)

            # We need to look on this page for links we haven't been to yet
            frontier.update(fetch_urls(page))
            
    # Print all found flags
    print_flags()

crawl()
