from ferris.core import inflector
from settings import app_config
from google.appengine.ext import blobstore, ndb
import wtforms
import logging
import cgi


class Upload(object):
    """
    Automatically handles file upload fields that need to use the blobstore.

    This works by:
    * Detecting if you're on an add or edit action (you can add additional actions with ``upload_actions``, or set ``process_uploads`` to True)
    * Adding the ``upload_url`` template variable that points to the blobstore
    * Updating the ``form_action`` and ``form_encoding`` scaffolding variables to use the new blobstore action
    * Processing uploads when they come back
    * Adding each upload's key to the form data so that it can be saved to the model

    Does not require that the handler subclass ``BlobstoreUploadHandler``, however to serve blobs you must subclass ``BlobstoreDownloadHandler``.
    """

    def __init__(self, handler):
        self.handler = handler
        self.__uploads = None
        self.process_uploads = False
        self.upload_actions = ('add', 'edit')
        self.gs_bucket_name = None

        handler.events.before_startup += self.on_before_startup
        handler.events.scaffold_before_apply += self.on_scaffold_before_apply
        handler.events.after_dispatch += self.on_after_dispatch

    def on_before_startup(self, handler):
        if handler.action in self.upload_actions:
            self.process_uploads = True

    def on_scaffold_before_apply(self, handler, form, item):
        if self.process_uploads:
            self.process(form)

    def on_after_dispatch(self, handler, response):
        """
        This will additionally check if ?start is the query string. If so, it will return just the upload url. This is
        great for rest apis.
        """
        if self.process_uploads:
            if not handler.get('upload_url'):
                handler.set(upload_url=self.generate_upload_url(self.handler.action))
                if hasattr(handler, 'scaffold'):
                    handler.scaffold.form_action = handler.get('upload_url')
                    handler.scaffold.form_encoding = 'multipart/form-data'

            if 'start' in handler.request.params:
                if not response:
                    handler.set(data=handler.get('upload_url'))
                    if 'json' in handler.components:
                        handler.components.json.render()

    def process(self, form, item=None):
        """
        Process all of the incoming file upload and populate the form with them.
        Only processes file fields that are present in the form
        """
        for field in [x for x in form if isinstance(x, wtforms.fields.FileField)]:
            files = self.get_uploads(field.name)
            if files and files[0]:
                getattr(form, field.name).data = files[0].key()
            else:
                delattr(form, field.name)

    def generate_upload_url(self, action=None):
        if not action:
            action = self.handler.action

        return blobstore.create_upload_url(
                success_path=self.handler.uri(action=action, _pass_all=True, _full=True),
                gs_bucket_name=self.gs_bucket_name
            )

    def serve(self, item, property):
        if not item:
            return 404

        self.handler.send_blob(getattr(item, property))

        return self.handler.response

    def get_uploads(self, field_name=None):
        """Get uploads sent to this handler.

        Args:
        field_name: Only select uploads that were sent as a specific field.

        Returns:
        A list of BlobInfo records corresponding to each upload.
        Empty list if there are no blob-info records for field_name.
        """
        if self.__uploads is None:
            self.__uploads = {}
            for key, value in self.handler.request.params.items():
                if isinstance(value, cgi.FieldStorage):
                    if 'blob-key' in value.type_options:
                        info = blobstore.parse_blob_info(value)
                        self.__uploads.setdefault(key, []).append(info)

        if field_name:
            try:
                return list(self.__uploads[field_name])
            except KeyError:
                return []
        else:
            results = []
            for uploads in self.__uploads.itervalues():
                results += uploads
            return results
