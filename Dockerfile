FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 8000 8501
CMD ["bash","-lc","uvicorn app.api.main:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_ui/app.py --server.port 8501 --server.address 0.0.0.0"]
