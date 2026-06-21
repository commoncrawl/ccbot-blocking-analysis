S3PREFIX=s3://commoncrawl/projects/cc-open-athena-test/CC-SUPPLEMENTAL-2026-22

get-examples:
	mkdir -p CC-SUPPLEMENTAL-2026-22/segments/20260521074042/robotstxt/
	mkdir -p CC-SUPPLEMENTAL-2026-22/segments/20260521074042/crawldiagnostics/
	mkdir -p CC-SUPPLEMENTAL-2026-22/segments/20260521074042/warc/
	aws s3 cp $(S3PREFIX)/segments/20260521074042/robotstxt/CC-SUPPLEMENTAL-2026-22-20260521074116-20260521084116-00000.warc.gz CC-SUPPLEMENTAL-2026-22/segments/20260521074042/robotstxt/
	aws s3 cp $(S3PREFIX)/segments/20260521074042/crawldiagnostics/CC-SUPPLEMENTAL-2026-22-20260521074116-20260521084116-00000.warc.gz CC-SUPPLEMENTAL-2026-22/segments/20260521074042/crawldiagnostics/
	aws s3 cp $(S3PREFIX)/segments/20260521074042/warc/CC-SUPPLEMENTAL-2026-22-20260521074116-20260521084116-00000.warc.gz CC-SUPPLEMENTAL-2026-22/segments/20260521074042/warc/

segments:
	aws s3 ls $(S3PREFIX)/segments/ | awk '{sub(/\/$$/, "", $$2); print $$2}' > segments

files_robotstxt:
	aws s3 ls --recursive $(S3PREFIX)/segments/ | grep -v cdx | grep robotstxt | awk '{print $$4}' > files_robotstxt
files_crawldiagnostics:
	aws s3 ls --recursive $(S3PREFIX)/segments/ | grep -v cdx | grep crawldiagnostics | awk '{print $$4}' > files_crawldiagnostics
files_warc:
	aws s3 ls --recursive $(S3PREFIX)/segments/ | grep -v cdx | grep warc | awk '{print $$4}' > files_warc

all_files: files_robotstxt files_crawldiagnostics files_warc

# here is a table, it's sharded 10 ways
# aws s3 ls $(S3PREFIX)/index/table/cc-supplemental/warc/crawl=CC-SUPPLEMENTAL-2026-22/subset=robotstxt/

LOCALPREFIX=CC-SUPPLEMENTAL-2026-22/segments
SEGMENT=20260521074042

survey_http:
	python survey_http.py $(LOCALPREFIX)/$(SEGMENT)/robotstxt/*.gz > survey_robotstxt.out 2> survey_robotstxt_diag.out
	python survey_http.py $(LOCALPREFIX)/$(SEGMENT)/crawldiagnostics/*.gz > survey_crawldiagnostics.out 2> survey_crawldiagnostics_diag.out
	python survey_http.py $(LOCALPREFIX)/$(SEGMENT)/warc/*.gz > survey_warc.out 2> survey_warc_diag.out

sum_http:
	grep '^no match header ' survey_robotstxt_diag.out | cut -d ' ' -f4 | sort | uniq -c | sort -nr > http_sum_no_match_header_robotstxt.out
	grep '^no match header ' survey_crawldiagnostics_diag.out | cut -d ' ' -f4 | sort | uniq -c | sort -nr > http_sum_no_match_header_crawldiagnostics.out
	grep '^no match header ' survey_warc_diag.out | cut -d ' ' -f4 | sort | uniq -c | sort -nr > http_sum_no_match_header_warc.out

	grep '^no match cookie ' survey_robotstxt_diag.out | cut -d ' ' -f4 | sort | uniq -c | sort -nr > http_sum_no_match_cookie_robotstxt.out
	grep '^no match cookie ' survey_crawldiagnostics_diag.out | cut -d ' ' -f4 | sort | uniq -c | sort -nr > http_sum_no_match_cookie_crawldiagnostics.out
	grep '^no match cookie ' survey_warc_diag.out | cut -d ' ' -f4 | sort | uniq -c | sort -nr > http_sum_no_match_cookie_warc.out

	grep '^match header ' survey_robotstxt_diag.out | cut -d ' ' -f3 | sort | uniq -c | sort -nr > http_sum_match_header_robotstxt.out
	grep '^match header ' survey_crawldiagnostics_diag.out | cut -d ' ' -f3 | sort | uniq -c | sort -nr > http_sum_match_header_crawldiagnostics.out
	grep '^match header ' survey_warc_diag.out | cut -d ' ' -f3 | sort | uniq -c | sort -nr > http_sum_match_header_warc.out

	grep '^match cookie ' survey_robotstxt_diag.out | cut -d ' ' -f3 | sort | uniq -c | sort -nr > http_sum_match_cookie_robotstxt.out
	grep '^match cookie ' survey_crawldiagnostics_diag.out | cut -d ' ' -f3 | sort | uniq -c | sort -nr > http_sum_match_cookie_crawldiagnostics.out
	grep '^match cookie ' survey_warc_diag.out | cut -d ' ' -f3 | sort | uniq -c | sort -nr > http_sum_match_cookie_warc.out

sursurvey_robots_txt:
	python survey_robotstxt_txt.py $(LOCALPREFIX)/$(SEGMENT)/robotstxt/*.gz > survey_robotstxt_txt.out 2> survey_robotstxt_txt_diag.out
	grep '"location"' survey_robotstxt_txt.out > robots_redirs.out


# all segments of survey_robotstxt
# all segments of survey_robotstxt_txt

survey_all_robots_http:
	cat files_robotstxt | parallel -j25 python survey_http.py s3://commoncrawl {} > all_robotstxt.out 2> all_robotstxt_diag.out

survey_all_crawldiagnostics_http:
	cat files_crawldiagnostics | xargs -IFILE python survey_http.py s3://commoncrawl FILE > all_crawldiagnostics.out 2> all_crawldiagnostics_diag.out

survey_all_warc_http:
	cat files_warc | xargs -IFILE python survey_http.py s3://commoncrawl FILE > all_crawldiagostics.out 2> all_crawldiagostics_diag.out

survey_all_robots_txt:
	cat files_robotstxt | xargs -IFILE python survey_robotstxt_txt.py s3://commoncrawl FILE > all_robotstxt_txt.out 2> all_robotstxt_txt_diag.out

check_ADD_robotstxt:
	grep ADD all_robotstxt.out  | jq -c .kinds | sort | uniq -c | sort -nr

post-robotstxt:
	python post_robots_http.py all_robotstxt.out

post-robotstxt_txt:
	python post_robots_http.py all_robotstxt_txt.out
