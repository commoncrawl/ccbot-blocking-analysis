import sys
import json
import urllib

import fsspec
from warcio.archiveiterator import ArchiveIterator

import robots_class


indent = None
verbose = 0

robots_class.init_boilerplate()

s3prefix = sys.argv[1].rstrip('/') + '/'

if s3prefix.startswith('s3://'):
    start = 2
else:
    start = 1
    s3prefix = ''

for warc in sys.argv[start:]:
    with fsspec.open(s3prefix+warc, 'rb') as stream:
        ai = ArchiveIterator(stream)
        for record in ai:
            if record.rec_type == 'response':
                status = record.http_headers.get_statuscode()  # string
                uri = record.rec_headers.get_header('WARC-Target-URI')
                ip = record.rec_headers.get_header('WARC-IP-Address')
                date = record.rec_headers.get_header('WARC-Date')
                warc_headers = record.rec_headers.headers
                http_headers = record.http_headers.headers
                payload = record.content_stream().read().decode('utf-8', errors='replace')

                #offset = ai.get_record_offset()

                out = {'status': status, 'url': uri, 'date': date}

                if status == '200':
                    ret = robots_class.analyze_robots(uri, status, ip, http_headers, payload, verbose=verbose)
                    out['analysis'] = ret

                if status in {'301', '302', '303', '307', '308'}:
                    location = record.http_headers.get_header('Location')  # XXX this can fail
                    location = urllib.parse.urljoin(uri, location)
                    out['location'] = location

                print(json.dumps(out, indent=indent))
