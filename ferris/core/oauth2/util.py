import httplib2


def credentials_to_token(credentials):
    """
    Transforms an Oauth2 credentials object into an OAuth2Token object
    to be used with the legacy gdata API
    """
    import gdata.gauth

    credentials.refresh(httplib2.Http())
    token = gdata.gauth.OAuth2Token(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        scope=credentials.scope,
        user_agent='Google App Engine / Ferris Framework',
        access_token=credentials.access_token,
        refresh_token=credentials.refresh_token)
    return token


def get_discovery_document(api, api_version, uri_template="https://www.googleapis.com/discovery/v1/apis/{api}/{api_version}/rest", http=None):
    from ferris import cached
    if not http:
        http = httplib2.Http()

    uri = uri_template.format(api=api, api_version=api_version)

    @cached('gapi-discovery-doc-%s' % uri, 24*60*60)
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
