import urllib.parse
from collections import namedtuple

QuadData = namedtuple('QuadData', ['quad_url', 'quad_host', 'scheme_host'])


def make_quad(url):
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname

    # keeps the port
    url_tuple = (parts.scheme, parts.netloc, "", "", "")
    scheme_host = urllib.parse.urlunsplit(url_tuple)

    if host.startswith('www.'):
        # this is a cheat, but we probably don't care about 'www.com'
        host = host.replace('www.', '', 1)

    # keeps the port
    # XXX consider normalizing https plus :443 or http plus :80
    new_netloc = parts.netloc.replace(parts.hostname, host, 1)

    url_tuple = ('quad', new_netloc, "", "", "")
    quad_host = urllib.parse.urlunsplit(url_tuple)

    modified = parts._replace(
        scheme='quad',
        netloc=new_netloc,
    )
    quad_url = urllib.parse.urlunsplit(modified)

    return QuadData(
        quad_url=quad_url,
        quad_host=quad_host,
        scheme_host=scheme_host,
    )
