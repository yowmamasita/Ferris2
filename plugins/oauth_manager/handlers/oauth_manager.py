from ferris.core.controller import Controller, route
from ferris.core import scaffold
from ferris.core.oauth2.user_credentials import UserCredentials
from ferris.components import oauth
from apiclient.discovery import build
import wtforms
import logging


class AddForm(wtforms.Form):
    scopes = wtforms.TextAreaField(validators=[wtforms.validators.Required()], description='comma-separated')


class OauthManager(Controller):
    class Meta:
        prefixes = ('admin',)
        components = (scaffold.Scaffolding, oauth.OAuth)
        Model = UserCredentials

    class Scaffold:
        pass

    oauth_scopes = ['https://www.googleapis.com/auth/userinfo.profile']

    def startup(self):
        self.oauth.force_prompt = True

    @route
    @oauth.require_credentials
    def admin_test(self):
        http = self.oauth.http()
        service = build('oauth2', 'v2', http=http)

        user_info = service.userinfo().get().execute()

        self.context['user_info'] = user_info

    def admin_list(self):
        self.context['credentials'] = UserCredentials.query().order(-UserCredentials.admin)

    view = scaffold.view

    def admin_add(self):
        form = AddForm()
        self.process_form_data(form)

        if(self.request.method != 'GET' and form.validate()):
            scopes = map(lambda x: x.strip(), form.scopes.data.split(','))
            self.oauth.scopes = scopes
            return self.redirect(self.oauth._create_oauth_session(handler=self, admin=True, redirect=self.uri(action='list')))

        self.context['form'] = form

    admin_delete = scaffold.delete
