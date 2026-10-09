FROM python:3.13-slim
WORKDIR /app

# CPU-only torch first (avoids the multi-GB GPU build)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Build the data at image-build time: docs, chunks, FAISS indexes, model cache
RUN python -m app.ingest && python -m app.embed

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]