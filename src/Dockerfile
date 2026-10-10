FROM python:3.11-slim

WORKDIR /app/src

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY data /app/data

EXPOSE 8501
CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0"]
