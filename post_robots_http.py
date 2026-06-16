import sys
from collections import defaultdict

import orjson

import quad_class


# {"status": "200", "url": "http://0pointer.net/robots.txt", "date": "2026-05-21T07:44:14Z", "analysis": {"ignore me": 8, "Apache": 1, "Fedora": 1, "OpenSSL": 1}}
# {"status": "301", "url": "http://aberne41.wixsite.com/robots.txt", "date": "2026-05-21T07:43:00Z", "analysis": {"ignore me": 5}, "location": "https://aberne41.wixsite.com:443/robots.txt"}

status = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
outredir = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


with open(sys.argv[1], 'rb', buffering=1024*1024) as f:
    for line in f:
        record = orjson.loads(line)

        quads = quad_class.make_quad(record['url'])  # XXX can fail

        # status aggregation
        status[quads.quad_host]['status'][record['status']] += 1
        status[quads.quad_host][quads.scheme_host][record['status']] += 1

        if record['status'].startswith(('4', '5')) and record['status'] not in ('404', '410'):
            status[quads.quad_host]['bad_status']['all'] += 1

        if 'location' in record:
            location_quads = quad_class.make_quad(record['location'])  # XXX can fail
            # is the location quad host equal to the quad host
            if quads.quad_host != location_quads.quad_host:
                outredir[quads.quad_host][record['url']][record['location']] += 1
                status[quads.quad_host]['outredir'][record['location']] += 1

print('quad count', len(status))

quads_with_status = {}
for status_code in ('200', '404', '410'):
    quads_with_status[status_code] = len([status[x]['status'][status_code] for x in status if status[x]['status'][status_code]])
    print(f'quads with {status_code}: {quads_with_status[status_code]}')

print('quads with outredir', len(outredir))

bad_status = len([status[x]['bad_status']['all'] for x in status if status[x]['bad_status']['all']])
print('quads with bad status', bad_status)

ok_sum = sum(quads_with_status.values()) + len(outredir) + bad_status
print('all_sum', ok_sum)

# XXX how many quads have 1,2,3,4

# XXX how many quads have success and failure

# what is the list of failures
# if we run against robotstxt we have tech analysis available
# if we run against robotstxt_txt we have robots analysis available
