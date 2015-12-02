__author__ = 'christopherlyver'
import socket
import urlparse
import re

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


def get(url, cookies=None):
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
        session_id = cookies.get('session_id')
        get_request += "Set-Cookie: sessionid={}; csrftoken={}{}".format(session_id, csrf_token, crlf)

        get_request = "POST {} HTTP/1.0\{}".format(path, crlf) + \
                        "Host:fring.ccs.neu.edu:80\r\n" + \
        	            "Referer: http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/\r\n" + \
        	            "Set-Cookie:csrftoken="+csrf_token+"; sessionid="+session_id+"\r\n" + \
        	            "Connection:keep-alive\r\n" + \
        	            "Content-Type: application/x-www-form-urlencoded\r\n"
    print "******Sending GET Request:"
    print get_request
    sock.send(get_request)
    data = sock.recv(4096)

    sock.shutdown(1)
    sock.close()
    print "Get request responded with:  ******************"
    print data
    return data



def post(url, params):
    """
    Make a POST request to the given url, needed for authentication.
    """
    csrf_token = params.get('csrfmiddlewaretoken')
    sess_id = params.get('sessionid')

    new_sock = open_socket()
    http_params = "csrfmiddlewaretoken="+csrf_token+"&username="+username+"&password="+passwd+"&next=%2Ffakebook%2F"
    params_len = len(http_params)
    final_message = "POST /accounts/login/ HTTP/1.0\r\n" + \
                    "Host:fring.ccs.neu.edu:80\r\n" + \
		            "Referer: http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/\r\n" + \
		            "Cookie:csrftoken="+csrf_token+"; sessionid="+sess_id+"\r\n" + \
		            "Connection:keep-alive\r\n" + \
		            "Content-Type: application/x-www-form-urlencoded\r\n" + \
		            "Content-Length:{}\r\n\r\n".format(params_len) + \
                    http_params + "\r\n\r\n"
    print "Sending the following post request:"
    print final_message
    new_sock.sendall(final_message)
    response = new_sock.recv(4096)
    print "Response**************"
    print response
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


def run():
    print "Getting cookies..."
    csrf_cookie, session_id = get_cookies()
    print "*******Here are the cookies found - received csrf: {} and sessionId: {}".format(csrf_cookie, session_id)
    params = {'username': username,
              'password': passwd,
              'csrfmiddlewaretoken': csrf_cookie,
              'sessionid': session_id,
              'next': '/fakebook/'}
    print "*******Now logging in with those creds"
    auth_response = post(target_login, params)
    # The login page returns a new session id that we'll need moving forward
    cookie_jar = fetch_patterns(r"Set-Cookie\:(?:(?!;)(?:.|\n))*;", auth_response)
    final_session_id = cookie_jar[0].split('=')[1].split(';')[0]
    print "Our final session id {}".format(final_session_id)
    print "Going for the money..."
    res = get(target_domain, {'session_id': final_session_id, 'csrf_token': csrf_cookie})


run()
