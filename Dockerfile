FROM python:3.9
EXPOSE 8080
WORKDIR /app


# Copy Pipfile and Pipfile.lock (if available) to the working directory
COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

# Check if streamlit is installed and in PATH
RUN which streamlit

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]