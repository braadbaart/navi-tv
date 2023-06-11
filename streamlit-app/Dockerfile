FROM python:3.9-slim-buster
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "Navi_Demo.py", "--server.port", "8501"]