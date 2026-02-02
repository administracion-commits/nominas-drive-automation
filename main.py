import re
import io
import os

from pypdf import PdfReader, PdfWriter
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


# ========= CONFIGURACIÓN =========
PDF_ENTRADA = "nominas.pdf"

# ✅ ID REAL DE LA CARPETA DE DRIVE (el que confirmaste)
DRIVE_FOLDER_ID = "1K2kybinDirbmt6E8JavuILDhXENLN703"

# ✅ Scope correcto para crear/subir archivos
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
# =================================


def get_drive_service():
    """
    Autenticación OAuth usando refresh_token
    """
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=[DRIVE_SCOPE],
    )

    # Refresca el access token
    creds.refresh(Request())

    return build("drive", "v3", credentials=creds)


def validar_carpeta(drive):
    """
    Verifica que la carpeta existe y que tenemos acceso
    """
    info = drive.files().get(
        fileId=DRIVE_FOLDER_ID,
        fields="id, name, mimeType"
    ).execute()

    if info.get("mimeType") != "application/vnd.google-apps.folder":
        raise RuntimeError("El ID indicado NO corresponde a una carpeta de Drive")


def limpiar_nombre(nombre):
    """
    Elimina caracteres problemáticos para nombres de archivo
    """
    nombre = re.sub(r"[\\/:*?\"<>|]", "", nombre)
    return nombre.strip().replace(" ", "_")


def extraer_nombre(texto, indice):
    """
    Extrae el nombre del trabajador desde el texto del PDF
    """
    patron = r"TRABAJADOR\s*\(nombre\)\s*\n(.+)"
    match = re.search(patron, texto, re.IGNORECASE)

    if match:
        return limpiar_nombre(match.group(1))
    else:
        return f"pagina_{indice}"


def subir_pdf_a_drive(drive, nombre_archivo, buffer_pdf):
    """
    Sube un PDF NUEVO a Google Drive dentro de la carpeta indicada
    """
    buffer_pdf.seek(0)

    media = MediaIoBaseUpload(
        buffer_pdf,
        mimetype="application/pdf",
        resumable=False
    )

    drive.files().create(
        body={
            "name": nombre_archivo,
            "parents": [DRIVE_FOLDER_ID],
        },
        media_body=media,
        fields="id",
    ).execute()


def main():
    if not os.path.exists(PDF_ENTRADA):
        raise FileNotFoundError(f"No se encuentra el archivo {PDF_ENTRADA}")

    drive = get_drive_service()

    # 🔴 Validación dura de la carpeta
    validar_carpeta(drive)

    reader = PdfReader(PDF_ENTRADA)

    for i, page in enumerate(reader.pages, start=1):
        texto = page.extract_text() or ""
        nombre = extraer_nombre(texto, i)
        nombre_archivo = f"{nombre}.pdf"

        writer = PdfWriter()
        writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)

        subir_pdf_a_drive(drive, nombre_archivo, buffer)

        print(f"✔ Subido: {nombre_archivo}")


if __name__ == "__main__":
    main()
