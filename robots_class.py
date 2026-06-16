from urllib.robotparser import RobotFileParser


crawler_names = {
    'search_engines': [
        'googlebot',
        'googlebot-news',
        'bing',
        'meta-webindexer',
        'yandex',
        'slurp',
        'scoutjet',
    ],
    'ai_training': [
        'gptbot',
        'claudebot',
        'anthropic-ai',
        'google-extended',
        'googleother',
        'applebot-extended',
        'amazonbot',
        'bytespider',
        'ccbot',
        'cohere-ai',
        'mistralbot',
        'diffbot',
        'omgili',
        'dataforseobot',
        'grok',
        'grokbot',
        'xai-grok',
        'cloudflarebrowserrenderingcrawler',
        'meta-externalagent',
    ],
    'ai_rag_and_user': [
        'chatgpt-user',
        'oai-searchbot',
        'claude-web',
        'perplexitybot',
        'youbot',
        'grok-deepsearch',
    ],
    'social_media_ish': [
        'facebookbot',
        'twitterbot',
        'facebookexternalhit',
    ]
}

boilerplate = {
    # most matches are 20 lines, a few are 16. so this preamble has changed over time.
    'cloudflare_preamble': '''\
# As a condition of accessing this website, you agree to abide by the following
# content signals:

# (a)  If a Content-Signal = yes, you may collect content for the corresponding
#      use.
# (b)  If a Content-Signal = no, you may not collect content for the
#      corresponding use.
# (c)  If the website operator does not include a Content-Signal for a
#      corresponding use, the website operator neither grants nor restricts
#      permission via Content-Signal with respect to the corresponding use.

# The content signals and their meanings are:

# search:   building a search index and providing search results (e.g., returning
#           hyperlinks and short excerpts from your website's contents). Search does not
#           include providing AI-generated search summaries.
# ai-input: inputting content into one or more AI models (e.g., retrieval
#           augmented generation, grounding, or other real-time taking of content for
#           generative AI search answers).
# ai-train: training or fine-tuning AI models.

# ANY RESTRICTIONS EXPRESSED VIA CONTENT SIGNALS ARE EXPRESS RESERVATIONS OF
# RIGHTS UNDER ARTICLE 4 OF THE EUROPEAN UNION DIRECTIVE 2019/790 ON COPYRIGHT
# AND RELATED RIGHTS IN THE DIGITAL SINGLE MARKET.
''',
    'cloudflare_managed_start': '# BEGIN Cloudflare Managed content',
    'cloudflare_managed_end': '# END Cloudflare Managed Content',
}


def init_boilerplate():
    d = {}
    for k, v in boilerplate.items():
        v = v.splitlines()
        # get rid of blank lines
        boilerplate[k] = set([x for x in v if x != ''])


def analyze_robots(uri, status, ip, http_headers, payload, verbose=0):
    ret = {}
    lines = payload.splitlines()
    rp = RobotFileParser()
    rp.parse(lines)

    if rp.site_maps():
        ret['sitemaps'] = True

    for k, v in boilerplate.items():
        count = 0
        for line in lines:
            if line in v:
                count += 1
        if count:
            ret['boilerplate_' + k] = count

    global_disallow = not rp.can_fetch('*', '/')
    if global_disallow:
        ret['global_disallow_all'] = True
        # unlike global crawl delay, this doesn't cause downstream damage
    global_c_d = rp.crawl_delay('*')  # float
    if global_c_d:
        # this will cause overmatch, all tested uas will get this same delay even if they are not mentioned
        ret['global_crawl_delay'] = global_c_d

    for k, v in crawler_names.items():
        assert k != 'global'
        for ua in v:
            if not global_disallow:
                if not rp.can_fetch(ua, '/'):  # XXX fooled by /$
                    ret[ua + '_disallow_all'] = True
            else:
                # only look for allows or non-disallows if there is a global disallow
                if rp.can_fetch(ua, '/'):  # XXX fooled by /$
                    ret[ua + '_allow_all'] = True
            c_d = rp.crawl_delay(ua)
            if c_d and c_d != global_c_d:  # kinda fixup overmatching
                ret[ua + '_crawl_delay'] = c_d

    return ret
