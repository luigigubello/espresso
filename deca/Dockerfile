FROM python:3.11.6-bullseye

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["uvicorn", "server:app", "--host=0.0.0.0", "--port=8080"]