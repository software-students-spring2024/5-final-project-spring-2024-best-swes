# docs: https://hub.docker.com/_/python
FROM python:3.8-slim-buster

WORKDIR /web_app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]