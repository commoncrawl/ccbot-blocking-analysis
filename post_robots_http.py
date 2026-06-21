import sys
from collections import defaultdict

import orjson

import quad_class

# robotstxt
# {"status": "200", "url": "http://0pointer.net/robots.txt", "date": "2026-05-21T07:44:14Z", "analysis": {"ignore me": 8, "Apache": 1, "Fedora": 1, "OpenSSL": 1}}

# robotstxt_txt
# {"status": "200", "url": "http://0pointer.net/robots.txt", "date": "2026-05-21T07:44:14Z", "analysis": {"ignore me": 8, "Apache": 1, "Fedora": 1, "OpenSSL": 1}}
# {"status": "301", "url": "http://aberne41.wixsite.com/robots.txt", "date": "2026-05-21T07:43:00Z", "analysis": {"ignore me": 5}, "location": "https://aberne41.wixsite.com:443/robots.txt"}

status = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
outredir = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

waf_blocked = defaultdict(set)
waf_not_blocked = defaultdict(set)

nowaf_blocked = set()

with open(sys.argv[1], 'rb', buffering=1024*1024) as f:
    for line in f:
        record = orjson.loads(line)

        quads = quad_class.make_quad(record['url'])  # XXX can fail

        # status aggregation
        status[quads.quad_host]['status'][record['status']] += 1
        status[quads.quad_host][quads.scheme_host][record['status']] += 1

        # block
        if record['status'].startswith(('4', '5')) and record['status'] not in ('404', '410'):
            status[quads.quad_host]['bad_status']['all'] += 1
            if 'kinds' in record:
                # only robotstxt -- not present for robotstxt_txt
                if 'Web Application Firewall' in record['kinds']:
                    for k in record['kinds']['Web Application Firewall']:
                        waf_blocked[k].add(quads.quad_host)
                else:
                    nowaf_blocked.add(quads.quad_host)

        # not blocked
        if record['status'] in ('200', '404', '410'):
            status[quads.quad_host]['good_status']['all'] += 1
            if 'kinds' in record:
                if 'Web Application Firewall' in record['kinds']:
                    for k in record['kinds']['Web Application Firewall']:
                        waf_not_blocked[k].add(quads.quad_host)

        # redirect
        if 'location' in record:
            location_quads = quad_class.make_quad(record['location'])  # XXX can fail
            # is the location quad host equal to the quad host
            if quads.quad_host != location_quads.quad_host:
                outredir[quads.quad_host][record['url']][record['location']] += 1
                status[quads.quad_host]['outredir'][record['location']] += 1
                #status[quads.quad_host]['outredir']['all'] += 1

        # all records should have this
        if 'analysis' in record:
            # robotstxt
            if any('CloudFlare' in k for k in record['analysis']):
                status[quads.quad_host]['cloudflare tech'] = True

            # robotstxt_txt
            cf_seen = any('cloudflare' in k for k in record['analysis'])
            if cf_seen:
                status[quads.quad_host]['cloudflare tech'] = True

            if any('global_disallow_all' in k for k in record['analysis']):
                status[quads.quad_host]['global robots disallow'] = True
                if cf_seen:
                    status[quads.quad_host]['cf global robots disallow'] = True
            if any('gptbot_disallow_all' in k for k in record['analysis']):
                status[quads.quad_host]['gptbot robots disallow'] = True
                if cf_seen:
                    status[quads.quad_host]['cf gptbot robots disallow'] = True
            if any('ccbot_disallow_all' in k for k in record['analysis']):
                status[quads.quad_host]['ccbot robots disallow'] = True
                if cf_seen:
                    status[quads.quad_host]['cf ccbot robots disallow'] = True


print('quad count', len(status))
print('quad cloudflare count', sum(True for x in status if status[x].get('cloudflare tech', False)))

quads_with_status = {}
for status_code in ('200', '404', '410'):
    quads_with_status[status_code] = len([True for x in status if status[x]['status'][status_code]])
    print(f'quads with {status_code}: {quads_with_status[status_code]}')

print('quads with outredir', len(outredir))

bad_status = len([True for x in status if status[x]['bad_status']['all']])
print('quads with bad status', bad_status)

good_and_bad = len([status[x]['status'][status_code] for x in status if status[x]['bad_status']['all'] and status[x]['good_status']['all']])
print('quads that are both good and bad', good_and_bad)
#for x in status:
#    if status[x]['bad_status']['all'] and status[x]['good_status']['all']:
#        print(x, status[x])

multiple_outredir = len([True for x in status if len(status[x]['outredir']) > 1])
print('multiple outredir', multiple_outredir)

cf_bad_status = len([True for x in status if status[x]['bad_status']['all'] and status[x]['cloudflare tech']])
print('quads with cf bad status', cf_bad_status)

cf_origin_failing = {'520', '521', '522', '523','524', '525', '526', '527','530'}  # not blocks
cf_blocked = 0
for x in status:
    if not(status[x]['bad_status']['all'] and status[x]['cloudflare tech']):
        continue

    status_codes = status[x]['status']
    blocked = 0
    origin_problem = 0
    for s in status_codes:
        if s.startswith(('4', '5')) and s not in {'404', '410'} and s not in cf_origin_failing:
            blocked += 1
    if blocked:
        cf_blocked += 1
print(' quads with cf blocked status', cf_blocked)

for thing in ('global robots disallow', 'cf global robots disallow',
              'gptbot robots disallow', 'cf gptbot robots disallow',
              'ccbot robots disallow', 'cf ccbot robots disallow'):
    foo = sum(status[x].get(thing, False) for x in status)
    print(thing, foo)

all_wafs = set(waf_blocked)
all_wafs.update(set(waf_not_blocked))
sum_blocked = 0
sum_not_blocked = 0
for waf in sorted(all_wafs):
    blocked = len(waf_blocked[waf])
    not_blocked = len(waf_not_blocked[waf])
    pct = round(100 * blocked / (blocked + not_blocked))
    print('WAF blocked / not blocked', waf, blocked, '/', not_blocked, '('+str(pct)+'%)')
    sum_blocked += blocked
    sum_not_blocked += not_blocked
pct = round(100 * sum_blocked / (sum_blocked + sum_not_blocked))
print('WAF blocked / not blocked sums', sum_blocked, '/', sum_not_blocked,'('+str(pct)+'%)')

print('blocked but no visible WAF', len(nowaf_blocked))
print('  ', '\n  '.join(x for x in nowaf_blocked))

'''
robotstxt
quad count 9757
quad cloudflare count 1738
quads with 200: 6638
quads with 404: 2113
quads with 410: 5
quads with outredir 523
quads with bad status 729
quads that are both good and bad 115 <====
multiple outredir 2
quads with cf bad status 179
 quads with cf blocked status 162
WAF blocked / not blocked Amazon Cloudfront bots 6 / 0 (100%)
WAF blocked / not blocked Azure Front Door 3 / 27 (10%)
WAF blocked / not blocked BIG-IP Application Security Manager (F5 Networks) 1 / 140 (1%)
WAF blocked / not blocked Barracuda Load Balancer ADC and WAF 0 / 3 (0%)
WAF blocked / not blocked CleanTalk 0 / 1 (0%)
WAF blocked / not blocked CloudFlare-bot 94 / 586 (14%)
WAF blocked / not blocked CloudProxy WebSite Firewall (Sucuri) 2 / 24 (8%)
WAF blocked / not blocked DDoS-Guard 2 / 4 (33%)
WAF blocked / not blocked Ergon Airlock WAF 0 / 1 (0%)
WAF blocked / not blocked Generic WAF 0 / 21 (0%)
WAF blocked / not blocked Incapsula 3 / 31 (9%)
WAF blocked / not blocked QRATOR Labs WAF 1 / 7 (12%)
WAF blocked / not blocked Stingray Application Firewall (Riverbed / Brocade) 0 / 2 (0%)
WAF blocked / not blocked Wordfence WordPress Plugins 0 / 1 (0%)
WAF blocked / not blocked Zenedge Cybersecurity Suite (Oracle) 0 / 2 (0%)
WAF blocked / not blocked sums 112 / 850 (12%)
blocked but no visible WAF 1
   quad://philsci.com

robotstxt
quad count 9757
quad cloudflare count 256
quads with 200: 6638
quads with 404: 2113
quads with 410: 5
quads with outredir 523
quads with bad status 729
quads that are good and bad 0
multiple outredir 2
quads with cf bad status 179
 quads with cf blocked status 162
'''

'''
quad count 9757
quad cloudflare count 256
quads with 200: 6638
quads with 404: 2113
quads with 410: 5
quads with outredir 523
quads with bad status 729
quads that are good and bad 0
multiple outredir 2
global robots disallow 120
 cf global robots disallow 0
gptbot robots disallow 425
 cf gptbot robots disallow 192
ccbot robots disallow 299
 cf ccbot robots disallow 192
'''
