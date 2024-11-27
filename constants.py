BUCKET_NAME = "ue4_ndlk_nonprod_stg_gcs_iadev_artfsto"
SUBFOLDER = "generativeai-downloads/pdf/asesor ventas"
PUBSUB_XLSX_TOPIC_NAME = "talenbot-xlsx-topic"
PUBSUB_PDF_TOPIC_NAME = "talenbot-pdf-topic"

LOGO_PATH = "assets/Talentbot-logo-v3-removebg-preview.png"
MAX_NUM_PDFS = 10
MAX_NUM_XLSX_ROWS = 50

XLSX_ROW_RUNTIME = 0.5

PDF_FORMATS = ['pdf', 'PDF']

XLSX_HEADERS = {
    "FILE_URL": "Adjuntar tu CV:",
    "SENT_TIME": "sent_timestamp"
}

API_URLS = {
    "auth": "https://bots-user-management-api-uwr3p4egga-uk.a.run.app",
}

ALLOWED_ROL = "talent-bot"
