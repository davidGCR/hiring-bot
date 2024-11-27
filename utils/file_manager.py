from constants import SUBFOLDER, BUCKET_NAME
import streamlit as st
from utils.utils import *

class FileObjectSet:
    def __init__(self):
        self.file_set = []
    
    def add_and_upload(self, uploaded_files_widget):
        """
        Add a new FileObject to the set.
        If the URI exists, do nothing if it is already in the set.
        If the URI is missing, update the existing object with the same name if it exists.
        """
        for i, upload_obj in enumerate(uploaded_files_widget):
            destination_blob_name = f"{SUBFOLDER}/{upload_obj.name}"
            print(f"===> upload object {i} : {upload_obj}, blob_name: {destination_blob_name}")
            uri = f"gs://{BUCKET_NAME}/{destination_blob_name}"
            self.file_set.append(uri)
        
        print(f"File SET: {self.file_set}")
        st.session_state.file_uploader_key += 1
        # st.rerun()
            
        # if uploaded_file_object_uri not in self.file_set:
        #         self.file_set.add(uploaded_file_object_uri)
        # else:
        #     print(f"URI {uploaded_file_object_uri} already exists.")

