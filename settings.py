
app_config = {}

app_config['timezone'] = 'US/Eastern'

app_config['email'] = {
    # Configures what address is in the sender field by default.
    'sender': None
}

app_config['webapp2_extras.sessions'] = {
    # WebApp2 encrypted cookie key
    # You can use a UUID generator like http://www.famkruithof.net/uuid/uuidgen
    'secret_key': '9a788030-837b-11e1-b0c4-0800200c9a66',
}

app_config['oauth2'] = {
    # OAuth2 Configuration should be generated from
    # https://code.google.com/apis/console
    'client_id': None,  # XXXXXXXXXXXXXXX.apps.googleusercontent.com
    'client_secret': None
}

# This enables the template debugger.
# It is automatically disabled in the live environment as it may leak sensitive data.
# Users in the 'required_domain' may view the debugger in the live environment.
app_config['ed_rooney'] = {
    'enabled': True,
    'required_domain': 'cloudsherpas.com'
}
