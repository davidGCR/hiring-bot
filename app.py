import streamlit as st
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
from utils.utils import (
    initialize_session_state, save_xlsx, get_current_time,
    create_multimodal_message, display_instructions,
    log_event, pre_process_xlsx_df, process_row, publish_pdf,
    login_user,
    upload_to_gcs
)
from utils.widgets import send_prompt
import os
import time
from prompts import *
import pandas as pd
from constants import *
import vertexai
import logging
from streamlit_extras.add_vertical_space import add_vertical_space
import base64
from annotated_text import annotated_text
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed



load_dotenv(override=True)
APP_NAME = os.getenv("APP_NAME")
APP_VERSION = os.getenv("APP_VERSION")
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
MODEL_ID = os.getenv("MODEL_ID")

logging.basicConfig(level=logging.INFO)

st.set_page_config(
        page_title=f"{APP_NAME}-{APP_VERSION}",
        page_icon=LOGO_PATH,
        layout="wide",
    )

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "instructions" not in st.session_state:
    st.session_state.instructions = False

if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Login")
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        st.session_state.username = username

        if st.button("Login"):
            # role = get_user_role(username)
            # print(f"Rol: {role}")
            error_msm = "Credenciales Inválidas."
            
            # res = login_user(username, password)
            # print(f"login response: {res}")
            
            # if 'error' in res:
            #     st.error(error_msm)
            # elif ALLOWED_ROL not in res['user']['role']:
            #     st.error(error_msm + " No tiene permiso para acceder a este bot.")
            # elif 'user' in res:
            #     st.session_state.logged_in = True
            #     st.success("Login exitoso!")
            #     st.rerun()
            # else:
            #     st.error(error_msm + " Ocurrio un problema.")
            if username == 'admin' and password=='admin':
                st.session_state.logged_in = True
                st.success("Login exitoso!")
                st.rerun()

elif not st.session_state.instructions:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title(f"{APP_NAME}-{APP_VERSION}")
        st.write(f"Bienvenido a la DEMO de {APP_NAME}-{APP_VERSION}.")
        display_instructions()
        if st.button("Entendido!"):
            st.success("Empecemos!")
            st.session_state.instructions = True
            st.rerun()
# if False:
#     pass
else:
    vertexai.init(project=PROJECT_ID)
    
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }
    model = GenerativeModel(
        MODEL_ID,
        generation_config=generation_config,
        system_instruction=SYSTEM_INSTRUCTION_V2
    )
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    
    col1, col2 = st.columns([7, 2])
    with col1:
        st.title(f"{APP_NAME}-{APP_VERSION}")
    with col2:
        st.image(LOGO_PATH)
    # st.subheader("Demo")

    with st.expander("# ⚠️Instrucciones:", expanded=True):
        # st.write(
        #     """
        #     - Califica al candidato.
        #     - Compara los candidatos en una tabla resumen.
        #     - Dame el numero de DNI de <nombre>.
        #     - Que candidato domina mas lenguajes.
        # """
        annotated_text(
                ("👋 **Inicia siempre con un saludo. Ejemplo: Hola** ","", "#fea") #, ("Hola","tú", "#afa")
        )
        annotated_text(
            ("🚫 **No ingreses texto mientras respondo...**","", "#f2ab9b"),
        )
        annotated_text(
            ("🔄 **Si actualizas la página perderás tu chat actual**","", "#b2f29b"),
        )
        annotated_text(
            ("📊 **Recuerda: Despues de cargar un Excel, eliminalo!!!**","", "#b9bbf9"),
        )
        annotated_text(
            ("🚨 **Solo necesito CVs cortos 📑 (¡No documentos largos! ❌)**","", "#efb9f9"),
        )

    ############################################# Main #############################################
    # Initialize the session state variables
    initialize_session_state(model=model)

    def process_xlsx():
        st.session_state.confirmed_upload = True
    
    # rednderizar todo
    for message in  st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"].replace("$", "\$"))  # noqa: W605
    # inicializar promt
    prompt = st.chat_input("Como te puedo ayudar?")

    # if st.session_state.file_uploader_key in st.session_state:
    #     st.write(st.session_state[st.session_state.file_uploader_key])
# ---------------------------------------------------------------------------- #
#                                    Sidebar                                   #
# ---------------------------------------------------------------------------- #
    with st.sidebar:
        image_path = LOGO_PATH
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode()

        image_url = f"data:image/png;base64,{image_base64}"

        st.markdown(f"""
            <h1> <img src="{image_url}" alt="emoji" style="width:40px; vertical-align: middle;">{APP_NAME}-{APP_VERSION} App </h1>
        """, unsafe_allow_html=True)
        
        st.markdown(f'''
        ¡Hola! 👋 **{st.session_state.username}**. Soy tu asistente de contratación 🤖. Analizo y califico CVs para ayudarte a encontrar a los mejores candidatos 📄✨. 
        ''')
        
        add_vertical_space(1)
        
# ----------------------------- PDF upload widget ---------------------------- #
        def uploader_callback():
            print("------------- PDF callback")
            
        st.session_state.uploaded_pdfs_widget = st.file_uploader("Elija los CV de candidatos en PDF (max. 10)", 
                                                                  type="pdf", 
                                                                  accept_multiple_files=True, 
                                                                  key=st.session_state.file_uploader_key,
                                                                  on_change=uploader_callback)
        
        upload_pdf_container = st.container()
        # if st.button("Clear uploaded files"):
        #     st.session_state.file_uploader_key += 1
        
        def upload_one_cv(upload_obj):
            destination_blob_name = f"{SUBFOLDER}/{upload_obj.name}"
            print(f"===> upload object : {upload_obj}, blob_name: {destination_blob_name}")
            uri = upload_to_gcs(BUCKET_NAME, upload_obj, destination_blob_name)
            return uri
        
        def add_and_upload(uploaded_files_widget):
            file_uris = []
            if len(uploaded_files_widget)>0:
                with upload_pdf_container:
                    with st.spinner("Subiendo archivos ..."):
                        with ThreadPoolExecutor() as executor:
                            bar = st.progress(0)
                            placeholder = st.empty()
                            future_to_obj = {executor.submit(upload_one_cv, obj): obj for obj in uploaded_files_widget}
                            for idx, future in enumerate(as_completed(future_to_obj), start=1):
                                try:
                                    uri = future.result()
                                    file_uris.append(uri)
                                    print(f"Uploaded to {uri}")
                                    progress = idx / len(uploaded_files_widget)
                                    placeholder.text(f"{int(progress * 100)}%")
                                    bar.progress(progress)
                                except Exception as e:
                                    print(f"Failed to upload: {e}")
                st.session_state.uploaded_uris_set += file_uris            
                    
                    # for i, upload_obj in enumerate(uploaded_files_widget):
                    #     uri = upload_one_cv(upload_obj)
                    #     file_uris.append(uri)
                    
                    # print(f"File SET: {file_uris}")
                    # st.session_state.uploaded_uris_set += file_uris
            
            return file_uris
            
        if st.session_state.uploaded_pdfs_widget:
            if len(st.session_state.uploaded_pdfs_widget) > MAX_NUM_PDFS:
                st.error(f"No se pueden cargar más de {MAX_NUM_PDFS} archivos PDF.")
                st.toast(f"**No se pueden cargar más de {MAX_NUM_PDFS} archivos PDF!**", icon="😓")
                # time.sleep(0.5)
                # st.session_state.file_uploader_key += 1
                # st.rerun()
            # else:
            #     initialize_file_object_set(st.session_state.uploaded_pdfs_widget)
            #     print(f'uploaded_files_set: {st.session_state.uploaded_files_set}')
        
# ---------------------------- XLSX upload widget ---------------------------- #
        uploaded_xlsx = st.file_uploader(f"Suba candidatos por Excel (max. {MAX_NUM_XLSX_ROWS} registros)", 
                                         type="xlsx", 
                                         key=st.session_state.file_uploader_xlsx_key)
        if uploaded_xlsx != None:
            df = pd.read_excel(uploaded_xlsx, dtype=str)
            if len(df) > MAX_NUM_XLSX_ROWS:
                st.session_state.xlsx_df = None
                st.error(f"El archivo Excel no puede tener más de {MAX_NUM_XLSX_ROWS} filas.")
                # time.sleep(0.5)
                # st.session_state.file_uploader_xlsx_key += 1
                # st.rerun()
            else:
                st.session_state.uploaded_xlsx = uploaded_xlsx
                valid_df, invalid_df = pre_process_xlsx_df(df)
                #TODO show errors in xlsx
                st.session_state.xlsx_df = valid_df
        
        add_vertical_space(2)
            
# ---------------------------- Confirm XLSX upload --------------------------- #
    if st.session_state.uploaded_xlsx is not None and st.session_state.xlsx_df is not None:
        st.markdown(f"### Preview: ")
        st.markdown(f"#### 📄✨ ¡Se subirán {len(st.session_state.xlsx_df)} CVs en formato PDF! (⚠️ Archivos en MS Word no son soportados).")
        st.markdown(f"#### ✅ Por favor, confirme haciendo click en el botón para subir.")
        st.write(st.session_state.xlsx_df.head(10))

        if not st.session_state.confirmed_upload:
            if st.button("Confirmar carga de archivo"):
                st.session_state.processing_xlsx = True
                xlsx_uri = save_xlsx(st.session_state.uploaded_xlsx)
                st.session_state.xlsx_df[XLSX_HEADERS["SENT_TIME"]] = get_current_time()
                for index, row in st.session_state.xlsx_df.iterrows():
                    process_row(row)
                    
                log_event(event_type="user-message", user_id=st.session_state.username, message="Procesar xlsx", files=[{'file_name': xlsx_uri, 'file_type': 'application/xlsx'}])
                st.session_state.file_uploader_xlsx_key += 1
                st.rerun()

# --------------------------------- EXCEL LOAD BAR --------------------------------- #
    if st.session_state.processing_xlsx:
        df = st.session_state.xlsx_df
        total_rows = len(df)
        total_time = total_rows * XLSX_ROW_RUNTIME
        progress_text = "Procesando archivo, no ingrese texto..."
        my_bar = st.progress(0, text=progress_text)
        increments = 10  # Number of smaller updates per row
        increment_time = XLSX_ROW_RUNTIME / increments  # Time between smaller updates
        for i, row in df.iterrows():
            # Simulate processing time for each row
            for j in range(increments):
                # time.sleep(increment_time)
                progress = min(((i + j / increments) + 1) / total_rows, 1.0)  # Ensure progress does not exceed 1.0
                my_bar.progress(progress, text=f"{progress_text} ({int(progress * 100)}%)")
        
        st.success("⚙️ Estoy procesando los CVs en segundo plano! ⏱️ No te preocupes, podemos seguir charlando 💬 mientras lo hago. 🤖💬")
        # st.info("**⚠️ No te olvides de eliminar el archivo Excel que cargaste!**")
 
        st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"Procesando el archivo Excel: {st.session_state.uploaded_xlsx.name}..."
                    }
                )
        st.session_state.processing_xlsx = False
        st.session_state.xlsx_df = None

    
    #Chat
    if prompt:
        # Renderizar input del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        if prompt.isspace():
            with st.chat_message("assistant"):
                st.markdown("Ingresa un texto no vacio por favor.")
        else:
            # Renderizar response modelo
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                prompt += """, Responde en español, por favor."""
                with st.spinner("Respondiendo..."):
                    # new_files_uris = upload_files_without_uri()
                    file_uris = add_and_upload(st.session_state.uploaded_pdfs_widget)
                    multimodal_message, user_input, files_log = create_multimodal_message(file_uris=file_uris, prompt=prompt)
                    logging.info(f"===> user multimodal_message: {multimodal_message}")
                    # full_response = send_prompt(multimodal_message, file_uris)
                    full_response = send_prompt(multimodal_message, 
                                                message_placeholder, 
                                                generation_config, 
                                                safety_settings, 
                                                user_input, 
                                                files_log)
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": full_response,
                        }
                    )
                    for uri in file_uris:
                        publish_pdf(uri, full_response)
                
            if len(file_uris) > 0:
                st.session_state.file_uploader_key += 1
                st.rerun()
                    
