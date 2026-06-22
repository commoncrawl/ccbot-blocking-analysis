# bot-blocking in the Open Athena pilot crawl

## Intro

I revived some code from 2018 that fingerprints webservers.

Jargon: A "quad" is what we call the 4 related hosts of:
- http://example.com/
- https://example.com/
- http://www.example.com/
- https://www.example.com/

Since robots.txt is the first thing fetched in the crawl, there are
often redirects between these 4 things.

We're interested in if we got a robots.txt at all, did it disallow us,
and was Cloudflare seen at the scene of the crime.

This crawl had 9757 quads, of which 1758 (17%) had Cloudflare fingerprints.

## Overall

- 6638 quads had a robots.txt (status 200) (68%)
- 2118 quads had no robots.txt (404 or 410) (22%)
- 523 quads redirected us outside the quad; we did not analyze those (5%)

## Bot defenses

- 729 quads sent us error codes instead of 200/404/410 (7.5%) -- bot blocking?
  - of these, 179 had Cloudflare fingerprints
    - 162 of these were bot blocking
    - 17 were Cloudflare errors related to the "origin host" being down -- not bot blocking

## Web application firewall details (bot blocking)

- Amazon Cloudfront bots 6 / 0 (100%)
- Azure Front Door 3 / 27 (10%)
- BIG-IP Application Security Manager (F5 Networks) 1 / 140 (1%)
- Barracuda Load Balancer ADC and WAF 0 / 3 (0%)
- CleanTalk 0 / 1 (0%)
- CloudFlare 178 / 1472 (11%)
- CloudProxy WebSite Firewall (Sucuri) 2 / 24 (8%)
- DDoS-Guard 2 / 4 (33%)
- Ergon Airlock WAF 0 / 1 (0%)
- FortiWeb 0 / 8 (0%)
- Imperva 3 / 31 (9%)
- Mystery wafrule WAF 0 / 21 (0%)
- QRATOR Labs WAF 1 / 7 (12%)
- Stingray Application Firewall (Riverbed / Brocade) 0 / 2 (0%)
- Vercel hosted 1 / 49 (2%)
- Wordfence WordPress Plugins 0 / 1 (0%)
- Zenedge Cybersecurity Suite (Oracle) 0 / 2 (0%)
- sums 197 / 1793 (10%)

blocked but no visible WAF 14
- labroots.com
- implicit.harvard.edu
- ninds.nih.gov
- chenowethgroup.chem.upenn.edu
- help.ezbiocloud.net
- eurekalert.org
- statmethods.net
- armachelab.med.nyu.edu
- yeastgenome.org
- kim.bio.upenn.edu
- half-earthproject.org
- ling.upenn.edu
- confit.atlas.jp
- iadc-home.org

Analysis:
- 8 {"Amazon Elastic Load Balancer":1,"ignore me":3}
- 1 {"ignore me":8,"Apache":1,"Ubuntu":1}
- 1 {"ignore me":6,"Apache":1}
- 1 {"ignore me":5,"Apache":1,"CentOS":1}
- 1 {"ignore me":15,"Amazon Elastic Load Balancer":2,"Apache":1,"Amazon Cloudfront":5}
- 1 {"Amazon Elastic Load Balancer":3,"ignore me":3}
- 1 {"Amazon Elastic Load Balancer":1,"ignore me":4}

Ergo, 11/14 are actually Amazon something.

## robots.txt disallow

Of 6638 quads that sent us a robots.txt:

- 120 disallowed all bots -- mostly due to an "allowlist" strategy
  -  0 of those had Cloudflare fingerprints
- 425 disallowed GPTBot
  - 192 of these had Cloudflare fingerprints
- 299 disallowed CCBot
  - 192 of these had Cloudflare fingerprints

## Summary

- 729 quads of bot blocking is 7.5% of 9757 quads
- 120+299 CCBot robots.txt disallowed 4.3% of 9757 quads
- 64% of CCBot robots.txt disallowed has Cloudflare fingerprints

## Future TODO:

What technologies other than Cloudflare are commonly blocking CCBot?
