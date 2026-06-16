# cc-frobnicate

This code analyzes CCF's raw crawl and indexes.

## date-range combiner

given a thing, finds the earliest and latest

- robots.txt digest
  - robotstxt 200 url_host_name
  - ... or a chain of redirects, which should all be there
- successful crawls
  - 200 for homepages
  - ... or a chain of redirects leading to not / which won't be there
- underlying tech
  - 200 or redir
  - summarize headers and cookies
- ip addresses

## robots.txt classifier

given robots.txt, summarizes it

## tech classifier

Given inputs like http headers, warc headers, etc. figures out what technologies are used

- cdns like cloudflare
- cmses like wordpress
- wafs like cloudfront, akamai, fastly
- hosting services, like wordpress.com
- other
