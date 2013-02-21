from __future__ import absolute_import
from google.appengine.ext import ndb
from ferris.core.handler import Handler, route, route_with
from oauth2client.client import OAuth2WebServerFlow
from ferris.core.oauth2.user_credentials import UserCredentials as OAuth2UserCredentials
from settings import app_config


class Oauth(Handler):

    @route
    def start(self, session):
        if not app_config['oauth2']['client_id'] or not app_config['oauth2']['client_secret']:
            self.response.write("OAuth2 has not been configured in settings.py")
            return 500

        session = ndb.Key(urlsafe=session).get()
        callback_uri = self.uri(action='callback', _full=True)

        flow = OAuth2WebServerFlow(
            client_id=app_config['oauth2']['client_id'],
            client_secret=app_config['oauth2']['client_secret'],
            scope=session.scopes,
            redirect_uri=callback_uri)

        flow.params['state'] = session.key.urlsafe()

        if session.admin or session.force_prompt:
            flow.params['approval_prompt'] = 'force'

        uri = flow.step1_get_authorize_url()

        session.flow = flow
        session.put()

        return self.redirect(uri)

    @route_with(template='/oauth2callback')
    def callback(self):
        session = ndb.Key(urlsafe=self.request.params['state']).get()

        credentials = session.flow.step2_exchange(self.request.params['code'])

        # Delete any old credentials
        old_credentials = OAuth2UserCredentials.find_all(user=self.user, scopes=session.scopes, admin=session.admin)
        for x in old_credentials:
            x.key.delete()

        # Save the new ones
        user_credentials = OAuth2UserCredentials(
            user=self.user,
            scopes=session.scopes,
            credentials=credentials,
            admin=session.admin
        )

        user_credentials.put()
        session.key.delete()  # No need for the session any longer

        return self.redirect(str(session.redirect))
