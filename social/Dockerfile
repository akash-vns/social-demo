FROM python:3.8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
USER root
RUN python -m pip install --upgrade pip
RUN apt-get update --fix-missing

WORKDIR /code
COPY requirements.txt /code/
RUN chmod 777 /tmp

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/
