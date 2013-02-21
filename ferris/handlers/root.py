from ferris.core.handler import Handler, users


class Root(Handler):

    def root(self):
        self.template_name = 'index.html'

    def admin(self):
        if not users.is_current_user_admin():
            return 401
        self.template_name = 'admin_index.html'
