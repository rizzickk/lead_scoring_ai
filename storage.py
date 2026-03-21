import os
from supabase import create_client


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
SUPABASE_BUCKET = os.environ["SUPABASE_BUCKET"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_pdf_and_get_signed_url(file_bytes: bytes, file_name: str, expires_in: int = 86400) -> tuple[str, str]:
    path = f"reports/{file_name}"

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": "application/pdf"}
    )

    signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
        path=path,
        expires_in=expires_in
    )

    signed_url = signed.get("signedUrl") or signed.get("signedURL")
    return path, signed_url