import json

import robots_class


payload = open('robots.txt').read()


robots_class.init_boilerplate()
ret = robots_class.analyze_robots('', '', '', '', payload, verbose=0)


print(json.dumps(ret, indent=4))
