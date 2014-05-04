import httplib2


def get_discovery_document(api, api_version, uri_template="https://www.googleapis.com/discovery/v1/apis/{api}/{api_version}/rest", http=None):
    from ferris import caching
    if not http:
        http = httplib2.Http()

    uri = uri_template.format(api=api, api_version=api_version)

    @caching.cache_using_memcache('gapi-discovery-doc-%s' % uri, 24*60*60)
    def fetch():
        r, c = http.request(uri)
        return r, c

    r, c = fetch()

    return c


def patch_discovery():
    from apiclient import discovery
    original_build = discovery.build

    def patched_build(serviceName, version, http=None, **kwargs):
        doc = get_discovery_document(serviceName, version, http=http)
        return discovery.build_from_document(doc, http=http, **kwargs)

    discovery.build = patched_build
    setattr(discovery, '_build', original_build)


patch_discovery()
