FROM python:3.9-slim-buster
WORKDIR /app
COPY app/ app/
COPY pages/ pages/
COPY images/ images/
COPY Navi_TV.py .
COPY .streamlit/config.toml .streamlit/config.toml
COPY .streamlit/secrets.toml .streamlit/secrets.toml
COPY .streamlit/youtube-api.json .streamlit/youtube-api.json
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "Navi_TV.py", "--server.address", "0.0.0.0", "--server.port", "8501"]