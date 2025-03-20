# Hiring Bot

Chatbot in GCP to analyze candidate CVs for sales advisor positions. This solution aimed to streamline recruitment processes, reduce time-to-hire, and select top prospects with high retention and productivity potential. The system utilized techniques such as prompt engineering, Retrieval-Augmented Generation (RAG), and fine-tuning.

## Architecture

![Alt text](assets/architecture.png)

## Demo

![Demo of the Feature](assets/demo.gif)

## Setup
- Install Pipenv
- Update .env file

## Run locally

1. Create a service account file: llm.json
2. Install dependencies using pipenv
   ```bash
   pipenv install
   ```
3. Run the server
    ```shell
   # With pipenv
   pipenv run streamlit run app.py

   # With streamlit
   streamlit run app.py
    ```


