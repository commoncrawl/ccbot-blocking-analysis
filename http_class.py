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


def facet_to_kind(classifier, techs, kinds):
    # given a list of techs, pass back kinds that match kinds
    conf = classifier.configuration
    tmp = defaultdict(list)
    ret = {}

    for tech in techs:
        ks = conf[tech]['kind']
        for k in ks:
            if k in kinds:
                tmp[k].append(tech)
    for k in sorted(kinds):
        if k in tmp:
            ret[k] = tmp[k]
    return ret
