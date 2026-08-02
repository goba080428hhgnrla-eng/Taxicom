import os
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import Storage

from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)

BUCKET = os.getenv("SUPABASE_BUCKET")


class SupabaseStorage(Storage):

    def _save(self, name, content):

        carpeta = os.path.dirname(name)

        extension = os.path.splitext(name)[1]

        filename = f"{uuid.uuid4()}{extension}"

        if carpeta:
            filename = f"{carpeta}/{filename}"

        content.seek(0)

        supabase.storage.from_(BUCKET).upload(
            path=filename,
            file=content.read(),
            file_options={
                "content-type": getattr(
                    content,
                    "content_type",
                    "application/octet-stream",
                )
            },
        )

        return filename

    def delete(self, name):
        supabase.storage.from_(BUCKET).remove([name])

    def exists(self, name):
        return False

    def open(self, name, mode="rb"):

        data = supabase.storage.from_(BUCKET).download(name)

        return ContentFile(data)

    def url(self, name):

        response = (
            supabase.storage
            .from_(BUCKET)
            .create_signed_url(name, 60 * 60 * 24)
        )

        return response["signedURL"]