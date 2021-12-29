FROM python:3.8.12-buster
RUN pip install eth-brownie==1.17.2
RUN pip install psycopg2==2.8.6

COPY . /src/
WORKDIR /src/

CMD ["python", "-u", "faucet_worker.py"]