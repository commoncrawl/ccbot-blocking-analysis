import sys
import re
from collections.abc import Mapping
from urllib.parse import urlparse
from datetime import timedelta

#from progress.bar import Bar


def regex_to_non_regex(s):
    if s.startswith('^'):
        s = s[1:]
    i = 0
    for i in range(0, len(s)):
        if s[i] == '\\':  # ends with an incomplete escape,
            continue  # don't consider breaking it here
        if is_regex(s[:i+1]):
            break
    else:
        i += 1
    if i > 0:
        if i == len(s):
            original = True
        else:
            original = False
        if not original and s[i] == '?':
            # Whoopsie. Back up one.
            i -= 1
            original = False
        if not original and s[i-1] == '\\':
            # don't let it end wth an incomplete escape,
            # unless the string originally ended that way
            i -= 1
        non_regex = s[:i]
        if non_regex.endswith('/') and not original:  # XXX good for server: versions, no so good for urls
            non_regex = non_regex[:-1]
            if non_regex.endswith('\\'):  # and the escape, if present
                non_regex = non_regex[:-1]
        if non_regex.endswith(' '):
            non_regex = non_regex[:-1]
        if len(non_regex) > 2 and non_regex[-2] == ' ':
            non_regex = non_regex[:-2]

        return un_re_quote(non_regex)


not_regex_escapes = '.?\\/'
are_regex_escapes = '0123456789AZbBdDsSwW'
actual_regex_chars = '()?|[]^$.+*{}'


def re_quote(s):
    chars = list(s)
    ret = ''
    prev_slash = False
    for c in chars:
        if c in actual_regex_chars and not prev_slash:
            ret += '\\' + c
        else:
            ret += c
        if c == '\\':
            prev_slash = True
        else:
            prev_slash = False

    return ret


def un_re_quote(s):
    ret = ''
    chars = list(s)
    while len(chars) > 0:
        c = chars.pop(0)
        if c == '\\':
            if len(chars) == 0:
                ret += c
                break
            escape = chars.pop(0)
            if escape in actual_regex_chars:
                ret += escape
            else:
                ret += c + escape
        else:
            ret += c
    return ret


def is_regex(s):
    chars = list(s)
    while len(chars) > 0:
        c = chars.pop(0)
        if c == '\\':
            if len(chars) == 0:  # incomplete escape
                raise ValueError('incomplete escape '+s)
            escape = chars.pop(0)
            if escape in are_regex_escapes:
                return True
            elif escape in not_regex_escapes:
                continue
            elif escape in actual_regex_chars:
                continue
            else:
                print('saw an unknown escape of \\{} in {}'.format(escape, s), file=sys.stderr)
                continue
        elif c in actual_regex_chars:
            return True
    return False


def strip_extra_stuff(s):
    return s.split('\\;', 1)[0]


def classify_thing(s, cookie=False, link=False):
    # consider splitting regexes with | ? all of these have more than 1 :-(
    #   complex regex: contains '|' and more than one '(?:'

    # link: sometimes it's a domain name. .js is not currently a TLD.

    prefix, suffix = False, False
    original = s

    if cookie and s.endswith('='):
        s = s[:-1] + '$'
    if link and s.endswith('\\.js'):  # but these might have a query? or frag
        suffix = True
    if s.endswith('$'):
        suffix = True
        s = s[:-1]
    if s.startswith('^'):
        prefix = True
        s = s[1:]
    if link and (s.startswith('http://') or s.startswith('https://')):
        prefix = True

    if is_regex(s):
        return 'regex', original

    if prefix and suffix:
        return 'exact', s
    if prefix:
        return 'prefix', s
    if suffix:
        return 'suffix', s

    return 'infix', s


'''
Maching algorithm for each set

* big hash of the words, hopefully no collisions
* hash of prefixes for each length: 1 char, 2 chars, 3 chars, etc
    loop and hash probably faster than a big regex
* ditto for suffixes -- can use the same hash if we're being lazy

* for infix, big regex and re.findall
    since the individual things are not regex, the output from re.findall
    can be looked up in the big hash.

* for actual regex, build a huge regex, but how do you figure out which one
     matched? I suppose there won't be that many so I can try them
     one-by-one.

* for now treat everything as if it was exact, prefix, suffix, infix, discarding
all clues

'''


class MondoMatcher:
    def __init__(self, stuff, prefix=True, suffix=True, infix=True):
        # stuff is a dict of patterns and technologies
        self.prefix = prefix
        self.suffix = suffix
        self.all_dict = dict(stuff)

        if len(self.all_dict) != len(stuff):
            print('HEY GREG I dropped something', file=sys.stderr)
            dedup = set()
            for s, value in stuff:
                if s in dedup:
                    print('  dup is', s, value, file=sys.stderr)
                else:
                    dedup.add(s)

        self.maxlen_pre, self.len_pre = self._build_presuf(prefix)
        self.maxlen_suf, self.len_suf = self._build_presuf(suffix)

        # XXX temporary, there should not be dups
        dedup = set()
        deduped = []
        for k in self.all_dict:
            if k == '':
                # this is OK, for example 'Adblock Plus Whitelist' vs particular values of x-adblock-key
                continue
            k = re_quote(k)
            if is_regex(k):
                print('hey greg dropped regex', k, 'from infix', file=sys.stderr)
                continue
            if k not in dedup:
                deduped.append(k)
                dedup.add(k)
            else:
                print('hey greg key', k, 'was a dup in infix', file=sys.stderr)
        if infix:
            self.infix_pat = re.compile('|'.join(deduped))  # re_quote here after dedup code is removed
        else:
            self.infix_pat = None

    def _build_presuf(self, flag):
        if isinstance(flag, Mapping):
            d = flag
            raise ValueError('deprecated')
        elif not flag:
            return 0, {}
        else:
            d = self.all_dict

        maxlen = max([len(k) for k in d])
        length = {}
        for i in range(1, maxlen+1):
            length[i] = dict([(k, v) for k, v in d.items() if len(k) == i])

        return maxlen, length

    def match(self, s, exact_only=False):
        ret = []
        if s is None:
            return ret
        if s in self.all_dict:
            ret.append(self.all_dict[s])
        if exact_only:
            return ret

        if self.prefix:
            m = min(len(s), self.maxlen_pre)
            for i in range(m, 0, -1):  # longest to shortest
                probe = s[:i]
                if probe in self.len_pre[i]:
                    ret.append(self.len_pre[i][probe])
        if self.suffix:
            m = min(len(s), self.maxlen_suf)
            for i in range(m, 0, -1):  # longest to shortest
                probe = s[-i:]
                if probe in self.len_suf[i]:
                    ret.append(self.len_suf[i][probe])
        if self.infix_pat:
            m = self.infix_pat.findall(s)
            for pat in m:
                #hit = self.all_dict[pat]
                #if hit not in ret:
                #    print('infix was necessary for', repr(hit), ':', repr(s), file=sys.stderr)
                ret.append(self.all_dict[pat])

        ret = dedup(ret)
        return ret


def de_re_https(urls):
    ret = []
    for url in urls:
        if url.startswith('^'):
            # XXX remove me when we start handling prefixes
            url = url[1:]

        if url.startswith('https?://'):
            url = url[9:]
            ret.extend(('http://'+url, 'https://'+url))
            continue

        ret.append(url)

    return ret


def dedup(listt):
    # why isn't this a standard python thing?
    dedup = set()
    ret = []
    for element in listt:
        if element not in dedup:
            dedup.add(element)
            ret.append(element)
    return ret


def clean_utf8(s):
    try:
        s.encode()
    except UnicodeEncodeError:
        s = s.encode('utf-8', 'replace').decode()
    return s


def clean_facet_obj(obj):
    # cleverly, a few websites have non-USASCII bytes in things like cookie names.
    # this is a no-no and someone somewhere has encoded them as surrogates, which can't be printed
    if 'facets' in obj:
        for f in obj['facets']:
            if len(f) == 2:
                if isinstance(f[1], str):
                    f[1] = clean_utf8(f[1])
    if 'url' in obj:
        obj['url'] = clean_utf8(obj['url'])


def get_hostname(url):
    netloc = urlparse(url).netloc
    if ':' in netloc:
        return netloc.split(':', 1)[0]
    return netloc


def url_from_our_host(url, my_hostname):
    url_hostname = get_hostname(url)
    if url_hostname == my_hostname:
        return True
    if url_hostname.startswith('www.'):
        if url_hostname[4:] == my_hostname:
            return True
    else:
        if 'www.'+url_hostname == my_hostname:
            return True


#class IncrBar(Bar):
#    '''
#    A version of progress.Bar where updates aren't printed too often
#    '''
#    def __init__(self, *args, **kwargs):
#        if 'incr' in kwargs:
#            self.incr = kwargs['incr']
#        elif 'max' in kwargs:
#            self.incr = kwargs['max'] // 200  # around 0.5%
#        else:
#            self.incr = 1  # fall back to the usual behavior
#        self.incr_index = 0
#        super(IncrBar, self).__init__(*args, **kwargs)
#
#    def next(self, n=1):
#        self.incr_index += n
#        if self.incr_index >= self.incr or self.index + self.incr_index == self.max:
#            super(IncrBar, self).next(self.incr_index)
#            self.incr_index = 0
#
#    def goto(self, index):
#        super(IncrBar, self).next(self.incr_index)
#        self.incr_index = 0
#        super(IncrBar, self).goto(index)
#
#    @property
#    def stable_eta_td(self):
#        '''
#        A more-stable eta, especially later in the process
#        '''
#        progress = min(self.progress, 1.0)
#        seconds = int((self.elapsed + self.eta) * (1.0 - progress))
#        return timedelta(seconds=seconds)
