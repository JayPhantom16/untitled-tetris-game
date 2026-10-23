<<<<<<< HEAD
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
=======
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
>>>>>>> b8fdab76fa7ba2f49bb8fb796cf5ebd7d484c39e
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]