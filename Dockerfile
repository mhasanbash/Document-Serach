FROM python:3.14-slim

RUN mkdir /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip 

COPY ./requirments.txt .

RUN pip install --no-cache-dir -r requirments.txt

COPY ./backend backend/

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000 

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]