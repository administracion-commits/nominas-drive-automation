import re
import io
from pypdf import PdfReader, PdfWriter
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

PDF_ENTRADA = "FLEXO NOMINAS 012026.pdf"
DRIVE_FOLDER_ID = "PEGA_AQUI_TU_FOLDER_ID"
CREDS_FILE = "credentials.json"

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

reader = PdfReader(PDF_ENTRADA)
drive = get_drive_service()

for i, page in enumerate(reader.pages, 1):
    text = page.extract_text() or ""
    m = re.search(r"TRABAJADOR\s*\(nombre\)\s*\n(.+)", text)

    nombre = m.group(1).replace(",", "").replace(" ", "_") if m else f"pagina_{i}"
    filename = f"{nombre}.pdf"

    writer = PdfWriter()
    writer.add_page(page)

    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)

    media = MediaIoBaseUpload(buffer, mimetype="application/pdf")

    drive.files().create(
        body={"name": filename, "parents": [DRIVE_FOLDER_ID]},
        media_body=media,
        fields="id"
    ).execute()

print("Proceso terminado correctamente")
