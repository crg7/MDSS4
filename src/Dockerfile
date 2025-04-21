FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1

RUN apk add --update --no-cache postgresql-client
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev

# Instalar dependencias necesarias, incluidas las que Pillow necesita
RUN apk add -u zlib-dev jpeg-dev gcc musl-dev
RUN apk add zlib libjpeg-turbo-dev libpng-dev \
    freetype-dev lcms2-dev libwebp-dev \
    harfbuzz-dev fribidi-dev tcl-dev tk-dev

RUN python3 -m pip install --upgrade pip

COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

RUN apk del .tmp-build-deps

ENV HOME=/home/app
ENV APP_HOME=/home/app
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles

WORKDIR $APP_HOME

COPY ./webapp $APP_HOME
