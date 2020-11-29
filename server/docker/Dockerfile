FROM python:3.7-slim

WORKDIR /
COPY requirements.txt /server/requirements.txt
RUN pip3 install -r /server/requirements.txt

COPY . /server

CMD ["bash", "/server/docker/entrypoint.sh"]
