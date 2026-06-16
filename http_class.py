import sys

from collections import defaultdict

from facet_classifier import FacetClassifier


def init():
    Classifier = FacetClassifier('facet_config.json')
    return Classifier

# now we have:
# match_cookie(name, value)
# match_header(header, value)

def analyze_http(url, status, ip, http_headers, classifier, verbose=0):
    ret = defaultdict(int)
    match = []
    no_match = []
    multiple = True  # do not complain about multiple

    for header, value in http_headers:
        header = header.lower()
        if header == 'set-cookie':
            try:
                c, v = value.split('=', 1)
            except:
                if verbose:
                    print('cannot split http header', value, file=sys.stderr)
                continue
            kind = classifier.match_cookie(c, v, multiple=multiple)
            if kind:
                for k in kind:
                    ret[k] += 1
                    match.append(('match cookie', k, c, v))
            else:
                no_match.append(('no match cookie', c, v))
        else:
            kind = classifier.match_header(header, value, multiple=multiple)
            if kind:
                for k in kind:
                    ret[k] += 1
                    k = k.replace(' ', '-')
                    match.append(('match header', k, header, value))
            else:
                no_match.append(('no match header', header, value))

    if verbose > 1:
        for m in match:
            print(*m, file=sys.stderr)
    if verbose:
        for nm in no_match:
            print(*nm, file=sys.stderr)

    return ret
