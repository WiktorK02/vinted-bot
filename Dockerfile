FROM python:3.11-slim

WORKDIR /app

COPY vinted-bot.py .

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["python3", "vinted-bot.py"]  