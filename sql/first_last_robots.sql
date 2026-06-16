## Look for changes in robots.txt

SELECT
  url_host_name,
  content_digest,
  crawl,
  count(*) as robots_count,
  MIN(fetch_time) as fetch_time_min,
  MAX(fetch_time) as fetch_time_max
FROM ccindex
WHERE
  subset='robotstxt'
  AND crawl = 'CC-MAIN-2023-14' -- in -14, -23
  AND fetch_status = 200
  AND url_host_tld = 'com'
  AND url_host_name_reversed = 'com.nytimes.www'
GROUP BY
  url_host_name, content_digest, crawl

#	url_host_name	content_digest	crawl	robots_count	fetch_time_min	fetch_time_max
1	www.nytimes.com	4UBIWCGJ6BABOAIAZBYZUHJSUHDVAPC5	CC-MAIN-2023-14	105	2023-03-20 09:56:32.000	2023-04-02 10:58:05.000

#	url_host_name	content_digest	crawl	robots_count	fetch_time_min	fetch_time_max
1	www.nytimes.com	5QIURC7XFR3KNGI2CSX4UMTHAWNAWL5P	CC-MAIN-2023-23	105	2023-05-28 00:11:15.000	2023-06-11 00:27:25.000

## Look for the

SELECT
  url,
  fetch_time,
  url_host_name,
  content_digest,
  crawl,
  warc_file_name,
  warc_record_offset
FROM ccindex
WHERE
  subset='robotstxt'
  AND crawl = 'CC-MAIN-2023-14' -- in -14, -23
  AND url_host_tld = 'com'
  AND url_host_name_reversed = 'com.nytimes.www'
  AND content_digest = '5QIURC7XFR3KNGI2CSX4UMTHAWNAWL5P'
LIMIT 1

#	url	fetch_time	url_host_name	content_digest	crawl	warc_filename	warc_record_offset
1	https://www.nytimes.com/robots.txt	2023-03-20 09:56:32.000	www.nytimes.com	4UBIWCGJ6BABOAIAZBYZUHJSUHDVAPC5	CC-MAIN-2023-14	crawl-data/CC-MAIN-2023-14/segments/1679296943471.24/robotstxt/CC-MAIN-20230320083513-20230320113513-00339.warc.gz	1547589



#	url	fetch_time	url_host_name	content_digest	crawl	warc_filename	warc_record_offset
1	https://www.nytimes.com/robots.txt	2023-05-28 00:11:15.000	www.nytimes.com	5QIURC7XFR3KNGI2CSX4UMTHAWNAWL5P	CC-MAIN-2023-23	crawl-data/CC-MAIN-2023-23/segments/1685224643388.45/robotstxt/CC-MAIN-20230527223515-20230528013515-00339.warc.gz	1436607

warcio extract s3://commoncrawl/crawl-data/CC-MAIN-2023-14/segments/1679296943471.24/robotstxt/CC-MAIN-20230320083513-20230320113513-00339.warc.gz 1547589
- disallows Twitterbot, omgilibot, omgili, ia_archiver

warcio extract s3://commoncrawl/crawl-data/CC-MAIN-2023-23/segments/1685224643388.45/robotstxt/CC-MAIN-20230527223515-20230528013515-00339.warc.gz 1436607
- adds CCBot

So they added us explicitly between 2023-04-02 10:58:05.000 and 2023-05-28 00:11:15.000

## Crawl Explorer summary of our crawling as a csv -- based on the host index

Crawl,Date,Pages,Errors,Hosts,Is Aggregate,Num Crawls
CC-MAIN-2021-49,2021-12-06,53045,89830,103,false,1
CC-MAIN-2022-05,2022-01-31,2370,11312,31,false,1
CC-MAIN-2022-21,2022-05-23,3078,9755,41,false,1
CC-MAIN-2022-27,2022-07-04,1691,11110,15,false,1
CC-MAIN-2022-33,2022-08-15,2735,11020,6,false,1
CC-MAIN-2022-40,2022-10-03,2580,6915,8,false,1
CC-MAIN-2022-49,2022-12-05,3333,9692,8,false,1
CC-MAIN-2023-06,2023-02-06,3124,7182,8,false,1
CC-MAIN-2023-14,2023-04-03,2928,7702,8,false,1
CC-MAIN-2023-23,2023-06-05,127,1,5,false,1

