import urllib


def make_quad_url(url):
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname
    if host.startswith('www.'):
        # this is a cheat, but we probably don't care about 'www.com'
        host = host.replace('www.', '', 1)

    new_netloc = parts.netloc.replace(parts.hostname, host, 1)

    modified = parts._replace(
        scheme='quad',
        netloc=new_netloc,
    )

    return urllib.parse.urlunsplit(modified)


def make_quad_host(host):
    if host.startswith('www.'):
        # this is a cheat, but we probably don't care about 'www.com'
        host = host.replace('www.', '', 1)
    return 'quad://'+host
