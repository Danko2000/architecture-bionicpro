FROM apache/airflow:2.9.1-python3.9
USER root
RUN apt-get update && apt-get install -y gcc python3-dev libpq-dev && apt-get clean
USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt