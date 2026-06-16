import sys
import json
import urllib

import fsspec
from warcio.archiveiterator import ArchiveIterator

import http_class


indent = None
verbose = 2

classifier = http_class.init()

s3prefix = sys.argv[1].rstrip('/') + '/'

if s3prefix.startswith('s3://'):
    start = 2
else:
    start = 1
    s3prefix = ''

for warc in sys.argv[start:]:
    with fsspec.open(s3prefix+warc, 'rb') as stream:
        for record in ArchiveIterator(stream):
            if record.rec_type == 'response':
                status = record.http_headers.get_statuscode()  # string
                uri = record.rec_headers.get_header('WARC-Target-URI')
                ip = record.rec_headers.get_header('WARC-IP-Address')
                date = record.rec_headers.get_header('WARC-Date')
                warc_headers = record.rec_headers.headers
                http_headers = record.http_headers.headers
                #payload = record.content_stream().read().decode('utf-8', errors='replace')

                ret = http_class.analyze_http(uri, status, ip, http_headers, classifier, verbose=verbose)

                out = {'status': status, 'url': uri, 'date': date, 'analysis': ret}

                if status in {'301', '302', '303', '307', '308'}:
                    location = record.http_headers.get_header('Location')  # XXX this can fail
                    location = urllib.parse.urljoin(uri, location)
                    out['location'] = location

                print(json.dumps(out, indent=indent))
