__author__ = 'christopherlyver'
import webcrawler as crawler
import pdb

fb = 'fakebook/'
target_domain = 'http://fring.ccs.neu.edu/fakebook/'
html1 = ''
html2 = 'FLAG:flag1</h2>foofoofooFLAG:flag2</h2>barbarbar<a href="/fakebook/754857521/">'

# parse_flag() tests:
pattern = 'FLAG:my-flag</h2>'
assert crawler.parse_flag(pattern) == 'my-flag'

# fetch_flag_patterns() tests:
assert crawler.fetch_flag_patterns(html1) == []
assert crawler.fetch_flag_patterns(html2) == ['FLAG:flag1</h2>', 'FLAG:flag2</h2>']

# is_valid_url() test:
assert crawler.is_valid_url(fb)
good_url = fb + 'page1/sub-page1'
assert crawler.is_valid_url(good_url)
bad_url1 = 'wikipedia.org'
bad_url2 = 'facbook.com/{}'.format(target_domain)
assert not crawler.is_valid_url(bad_url1)
assert not crawler.is_valid_url(bad_url2)

# fetch_urls() test:
assert crawler.fetch_urls(html1) == []
#pdb.set_trace()
assert crawler.fetch_urls(html2) == ['fakebook/754857521/']
#print crawler.fetch_urls(html2)

# fetch_flags() tests:
assert not crawler.fetch_flags(html1)
assert crawler.fetch_flags(html2)

# print_flags() tests:
assert crawler.print_flags() == ['flag1', 'flag2']