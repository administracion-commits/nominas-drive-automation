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

# SOLO EL ID DE LA CARPETA (NO URL)
DRIVE_FOLDER_ID = "1Znmc-rOBjfXeVcd51xbU9GVq_oeRwRRl"

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
# =================================


def get_drive_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=[DRIVE_SCOPE],
    )

    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def extraer_nombre(texto, indice):
    """
    Extrae el nombre del trabajador desde nóminas con formato:
    TRABAJADOR (nombre)
    APELLIDOS, NOMBRE
    """
    # Normalizamos saltos de línea
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]

    for i, linea in enumerate(lineas):
        if re.search(r"TRABAJADOR\s*\(nombre\)", linea, re.IGNORECASE):
            if i + 1 < len(lineas):
                nombre = lineas[i + 1]

                # Limpieza del nombre
                nombre = nombre.replace(",", "")
                nombre = re.sub(r"[^\w\s]", "", nombre)

                return nombre.replace(" ", "_")

    # Fallback si no se encuentra
    return f"pagina_{indice}"


def subir_pdf_a_drive(drive, nombre_archivo, buffer_pdf):
    media = MediaIoBaseUpload(buffer_pdf, mimetype="application/pdf")

    drive.files().create(
        body={
            "name": nombre_archivo,
            "parents": [DRIVE_FOLDER_ID],
        },
        media_body=media,
        fields="id",
        supportsAllDrives=True,
    ).execute()


def main():
    reader = PdfReader(PDF_ENTRADA)
    drive = get_drive_service()

    for i, page in enumerate(reader.pages, start=1):
        texto = page.extract_text() or ""
        nombre = extraer_nombre(texto, i)
        nombre_archivo = f"{nombre}.pdf"

        writer = PdfWriter()
        writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        subir_pdf_a_drive(drive, nombre_archivo, buffer)
        print(f"✔ Subido: {nombre_archivo}")


if __name__ == "__main__":
    main()
