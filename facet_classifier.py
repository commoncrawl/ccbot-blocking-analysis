import sys
import os.path
import json
from collections import defaultdict
from urllib.parse import urlsplit
import itertools

import facet_utils
#import facet_preprocessing

things = set(('google analytics', 'google publisher id', 'google tag manager', 'facebook events', 'schema.org'))


class FacetClassifier:
    def __init__(self, f):
        if f is None:
            my_dir = os.path.split(__file__)
            f = os.path.join(*my_dir[:-1], 'facet_config')
        if not os.path.exists(f) and os.path.exists(f + '.json'):
            f += '.json'
        with open(f, 'r') as c:
            self._configuration = json.loads(c.read())

        self.cookie_mm = self.build_cookie()
        self.cname_mm = self.build_cname()
        self.header_mm, self.header_name_mm = self.build_multilevel('header')
        self.meta_mm, self.meta_name_mm = self.build_multilevel('meta')
        self.thing_mm, self.thing_name_mm = self.build_multilevel('thing')
        self.ipspecial_mm = self.build_ipspecial()
        self.ipasnorg_mm = self.build_ipasnorg()
        self.embed_mm, self.link_mm = self.build_url()
        self.tld_mm = self.build_tld()
        self.facet_mm, self.facet_name_mm = self.build_multilevel('facet')

    def _warn_multiple(self, ret, thing, value, multiple):
        if not multiple and len(ret) > 1:
            if len(ret) == 2 and (ret[0] == 'ignore me' or ret[1] == 'ignore me'):
                return
            print('Saw multiple return values for {} {}: {}'.format(thing, value, ret))

    def match_cookie(self, name, value, multiple=False):
        barracuda = False
        if name.startswith('BNES_'):  # thanks barracuda
            barracuda = True
            name = name[5:]
        if name.startswith('LB_'):  # thanks barracuda customer... another one out there with _website suffix
            barracuda = True
            name = name[3:]
        ret = self.cookie_mm.match(name)
        if barracuda:
            ret.append('Barracuda Load Balancer ADC and WAF')
        self._warn_multiple(ret, name, value, multiple)
        return ret

    def match_cname(self, name, multiple=False):
        ret = []
        name = name.lower()
        for cname in name.split(','):
            parts = cname.split('.')
            for i in reversed(range(len(parts))):
                # form candidates from longest to shortest. stop on first match.
                thing = itertools.islice(reversed(parts), i+1)
                partial = '.'.join(reversed(list(thing)))
                matches = self.cname_mm.match(partial)
                if matches:
                    ret.extend(matches)
                    break

        return ret

    def match_header(self, header, value, multiple=False):
        if header in self.header_mm:
            ret = self.header_mm[header].match(value)
            ret.extend(self.header_name_mm.match(header))
        else:
            ret = self.header_name_mm.match(header)
        self._warn_multiple(ret, header, value, multiple)
        return ret

    def match_meta(self, meta, value, multiple=False):
        if meta in self.meta_mm:
            tech = self.meta_mm[meta].match(value)
            tech.extend(self.meta_name_mm.match(meta, exact_only=True))
        else:
            tech = self.meta_name_mm.match(meta, exact_only=True)
        self._warn_multiple(tech, meta, value, multiple)
        return tech

    def match_thing(self, thing, value, multiple=False):
        if isinstance(value, bool):
            value = ''
        if thing in self.thing_mm:
            tech = self.thing_mm[thing].match(value)
            tech.extend(self.thing_name_mm.match(thing, exact_only=True))
        else:
            tech = self.thing_name_mm.match(thing, exact_only=True)
        self._warn_multiple(tech, thing, value, multiple)
        return tech

    def match_ipspecial(self, special, value, multiple=False):
        tech = self.ipspecial_mm.match(value)
        self._warn_multiple(tech, special, value, multiple)
        return tech

    def match_ipasnorg(self, ipasnorg, value, multiple=False):
        tech = self.ipasnorg_mm.match(value)
        self._warn_multiple(tech, ipasnorg, value, multiple)
        return tech

    def match_embed(self, embed):
        return self.embed_mm.match(embed)

    def match_link(self, link):
        return self.link_mm.match(link)

    def match_tld(self, url):
        hostname = urlsplit(url).netloc
        if ':' in hostname:
            hostname = hostname.split(':', 1)[0]
        if '.' in hostname:
            tld = '.' + hostname.split('.')[-1] + '/'
            return self.tld_mm.match(tld, exact_only=True)

    def match_facet(self, facet, value, multiple=False):
        if facet in self.facet_mm:
            ret = self.facet_mm[facet].match(value)
            ret.extend(self.facet_name_mm.match(facet))
        else:
            ret = self.facet_name_mm.match(facet)
        self._warn_multiple(ret, facet, value, multiple)
        return ret

    def build_cookie(self):
        all_cookies = []
        for technology, value in self._configuration.items():
            if 'cookies' in value:
                for c in value['cookies']:
                    if c.endswith('='):
                        c = c[:-1]
                    all_cookies.append((c, technology))
        return facet_utils.MondoMatcher(all_cookies)

    def build_cname(self):
        all_cnames = []
        for technology, value in self._configuration.items():
            if 'cnames' in value:
                for cname in value['cnames']:
                    all_cnames.append((cname, technology))
        return facet_utils.MondoMatcher(all_cnames, prefix=False, suffix=False, infix=False)

    def build_multilevel(self, k):
        all_foo = defaultdict(list)

        for technology, value in self._configuration.items():
            if k in value:
                for head in value[k]:
                    try:
                        header, value = head
                    except ValueError:
                        print('trouble unpacking', technology, k, head)
                        raise
                    all_foo[header.lower()].append((value, technology))

        foo_mm = {}
        foo_name = []

        for header in all_foo:
            if len(all_foo[header]) > 1:
                for value, technology in all_foo[header]:
                    if value == '':
                        # this is OK, e.g. google verification vs. particular values of it
                        foo_name.append((header, technology))
                foo_mm[header] = facet_utils.MondoMatcher(all_foo[header], suffix=False)
            else:
                value, technology = all_foo[header][0]
                if value != '':  # a singleton, but it stil has a value
                    foo_mm[header] = facet_utils.MondoMatcher(all_foo[header], suffix=False)
                else:
                    foo_name.append((header, technology))

        foo_name_mm = facet_utils.MondoMatcher(foo_name, suffix=False)

        return foo_mm, foo_name_mm

    def build_thing(self):
        facets = []
        for technology, value in self._configuration.items():
            if 'thing' in value:
                for thing in value['thing']:
                    facets.append((thing, technology))
        return facet_utils.MondoMatcher(facets)

    def build_ipspecial(self):
        facets = []
        for technology, value in self._configuration.items():
            if 'ip-special' in value:
                for special in value['ip-special']:
                    facets.append((special, technology))
        return facet_utils.MondoMatcher(facets, prefix=False, suffix=False)

    def build_ipasnorg(self):
        facets = []
        for technology, value in self._configuration.items():
            if 'ip-asn-org' in value:
                for ipasnorg in value['ip-asn-org']:
                    facets.append((ipasnorg, technology))
        return facet_utils.MondoMatcher(facets, prefix=False, suffix=False)

    def build_url(self):
        embed_urls = []
        embed_pre_urls = []
        link_urls = []
        link_pre_urls = []

        for technology, value in self._configuration.items():
            if 'embed' in value:
                for url in value['embed']:
                    embed_urls.append((url, technology))
            if 'link' in value:
                for url in value['link']:
                    link_urls.append((url, technology))

        embed_mm = facet_utils.MondoMatcher(embed_urls, prefix=embed_pre_urls, suffix=False)
        link_mm = facet_utils.MondoMatcher(link_urls, prefix=link_pre_urls, suffix=False)
        return embed_mm, link_mm

    def build_tld(self):
        tlds = []
        for technology, value in self._configuration.items():
            if 'tld' in value:
                for tld in value['tld']:
                    if not tld.startswith('.'):
                        raise ValueError('tld must start with period ' + technology + ' ' + tld)
                    if tld.endswith('/'):
                        raise ValueError('tld must not end with / ' + technology + ' ' + tld)
                    tlds.append((tld+'/', technology))
        return facet_utils.MondoMatcher(tlds, prefix=False, suffix=False)

    def _add_seealso(self, mytech, whys):
        to_process = list(mytech.keys())
        while True:
            new_this_cycle = []
            existing_mytech = mytech.copy()
            for tech in to_process:
                if 'seealso' in self._configuration[tech]:
                    for s in self._configuration[tech]['seealso']:
                        if s not in existing_mytech:
                            # only mark if it wasn't already marked -- .copy() means it's order-independent
                            whys.append(('seealso', tech, [s]))
                            new_this_cycle.append(s)
                        else:
                            whys.append(('seealso-notneeded', tech, [s]))
                        mytech[s] += 1
            if len(new_this_cycle) == 0:
                break
            to_process = new_this_cycle
        return whys

    def classify(self, obj, residue=False, seealso=True):
        residue_obj = {}
        whys = []

        if residue:
            residue_obj = obj.copy()
            if 'facets' in obj:
                residue_obj['facets'] = []

        mytech = defaultdict(int)
        if 'facets' in obj:
            if 'url' in obj:
                url = facet_utils.clean_utf8(obj['url'])

                ret = self.match_tld(url)
                if ret:
                    for r in ret:
                        mytech[r] += 1
                    whys.append(('tld', url, ret))

            dedup = set()
            if 'checksum' in obj:
                obj['facets'].append(['thing-content-checksum', obj['checksum']])
            for f, v in obj['facets']:
                # a lot of websites have exact duplicates, e.g. several of the same google verifies
                try:
                    fv = f + ' ' + v
                except TypeError:  # e.g. link-rel-canonical doesn't have a string value
                    pass
                else:
                    if fv in dedup:
                        continue
                    dedup.add(fv)

                multiple = False
                ret = []

                if f == 'header-set-cookie':
                    if v is None:
                        continue
                    cname, _, cvalue = v.partition('=')
                    ret = self.match_cookie(cname, cvalue)
                elif f == 'cnames':
                    ret = self.match_cname(v)
                elif f.startswith('header-'):
                    header = f[7:]
                    if header in ('server', 'x-powered-by',
                                  'x-powered-by-plesk', 'x-pantheon-styx-hostname'):
                        multiple = True
                    ret = self.match_header(header, v, multiple=multiple)
                elif f.startswith('meta-name-'):
                    name = f[10:]
                    if name == 'generator':
                        multiple = True
                    ret = self.match_meta(name, v, multiple=multiple)
                elif f.startswith('meta-property-'):
                    # Experiment: try to match this against the same matcher as meta-name
                    name = f[14:]
                    ret = self.match_meta(name, v, multiple=multiple)
                elif f.startswith('meta-http-equiv-'):
                    name = f[5:]  # http-equiv is part of the name
                    ret = self.match_meta(name, v, multiple=multiple)
                elif f.startswith('thing-'):
                    name = f[6:]
                    ret = self.match_thing(name, v)
                elif f.startswith('meta-http-equiv-refresh'):
                    ret = ['meta-http-equiv-refresh']
                elif f.startswith('meta-http-equiv-refresh-noscript'):
                    print('meta-http-equiv-refresh-noscript of {} for url {}'.format(v, url), file=sys.stderr)
                    ret = ['meta-http-equiv-refresh-noscript']
                elif f == 'ip-special':
                    name = f
                    ret = self.match_ipspecial(name, v)
                elif f == 'ip-asn-org':
                    name = f
                    ret = self.match_ipasnorg(name, v)
                else:
                    ret = self.match_facet(f, v)

                #ret.extend(facet_preprocessing.lexer((f, v)))

                ret = facet_utils.dedup(ret)  # XXX is this really needed? 1 cookie hitting PHP twice?
                if len(ret) > 1:
                    ret = [x for x in ret if x != 'ignore me']
                for tech in ret:
                    if tech == '':
                        print('GREG saw an empty tech for url', url, file=sys.stderr)  # hasn't happened in a while
                        continue
                    mytech[tech] += 1
                if residue and not ret:
                    residue_obj['facets'].append((f, v))
                if ret:
                    whys.append((f, v, ret))

        # we have all the techs for url:
        #facet_preprocessing.postprocess(mytech, whys, obj['facets'])

        for tech in list(mytech.keys()):
            if tech not in self._configuration:
                self._configuration[tech] = {'kind': ['ADD']}

                # suppress the most common ones
                if tech.startswith('cookie json-valued:'):
                    continue
                if tech.startswith('Mystery base64-encoded json start:'):
                    continue

                print(file=sys.stderr)  # make a new line to avoid the progress bar
                print('Making an entry for', tech, 'in the ADD category', file=sys.stderr)

        # exclude before seealso
        for tech in list(mytech.keys()):
            if 'excludes' in self._configuration[tech]:
                for e in self._configuration[tech]['excludes']:
                    if e in mytech:
                        del mytech[e]

        if seealso:
            whys = self._add_seealso(mytech, whys)

        dedup = set()
        new_whys = []
        new_whys_ignore_me = []
        for f, v, ret in whys:
            key = f+str(v)  # v might be a bool
            if not f.startswith('seealso') and key in dedup:  # don't dedup seealso
                continue
            dedup.add(key)
            if len(ret) == 1 and ret[0] == 'ignore me':
                new_whys_ignore_me.append((f, v, ret))
            else:
                new_whys.append((f, v, ret))
        whys = new_whys + new_whys_ignore_me

        return mytech, residue_obj, whys

    @property
    def configuration(self):
        return self._configuration
