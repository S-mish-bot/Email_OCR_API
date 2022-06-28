FROM python:3.8-buster

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

EXPOSE 5000

COPY . /app

CMD ["python3", "app.py"]



