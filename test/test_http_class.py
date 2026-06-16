import json

import http_class

classifier = http_class.init()

headers = open('http_headers.txt').read().splitlines()

new = []
for header in headers:
    try:
        h, v = header.split(':', 1)
    except:
        print('cannot split http header', header)
        continue
    new.append([h.strip(), v.strip()])
headers = new

ret = http_class.analyze_http('http://example.com/', '200', '', headers, classifier, verbose=2)

print(json.dumps(ret, indent=4))
