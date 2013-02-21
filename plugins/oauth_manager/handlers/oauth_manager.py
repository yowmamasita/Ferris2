from ferris.core.handler import Handler, scaffold, route
from ferris.core.oauth2.user_credentials import UserCredentials, ndb
from ferris.components import oauth
from apiclient.discovery import build
import wtforms
import logging


class AddForm(wtforms.Form):
    scopes = wtforms.TextAreaField(validators=[wtforms.validators.Required()], description='comma-separated')


@scaffold
class OauthManager(Handler):
    Model = UserCredentials
    prefixes = ['admin']
    components = [oauth.OAuth]

    oauth_scopes = ['https://www.googleapis.com/auth/userinfo.profile']

    def startup(self):
        self.oauth.force_prompt = True

    @route
    @oauth.require_credentials
    def admin_test(self):
        http = self.oauth.http()
        service = build('oauth2', 'v2', http=http)

        user_info = service.userinfo().get().execute()

        self.set(user_info=user_info)

    def admin_list(self):
        self.set(credentials=UserCredentials.query().order(-UserCredentials.admin))

    def admin_view(self, id):
        x = self.key_from_string(id).get()
        self.set(credentials=x)

    def admin_add(self):
        form = AddForm()
        self.process_form_data(form)

        if(self.request.method != 'GET' and form.validate()):
            scopes = map(lambda x: x.strip(), form.scopes.data.split(','))
            self.oauth.scopes = scopes
            return self.redirect(self.oauth._create_oauth_session(handler=self, admin=True, redirect=self.uri(action='list')))

        self.set(form=form)

    @scaffold
    def admin_delete(self, id):
        pass
