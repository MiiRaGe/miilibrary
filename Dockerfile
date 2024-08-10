FROM python:3.12.3-bullseye

RUN apt install tzdata

ADD requirements.txt /

RUN pip install --upgrade pip && pip install --no-input --upgrade --force-reinstall -r requirements.txt

ENV TZ=Europe/Stockholm

COPY . /app

WORKDIR /app

EXPOSE 5555
EXPOSE 8000