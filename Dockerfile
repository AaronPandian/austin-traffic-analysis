FROM ubuntu:20.04

RUN mkdir /APP

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y python3 \
		       python3-pip

COPY requirements.txt ./

RUN pip install -r requirements.txt

#COPY ./__init__.py /app/__init__.py

#COPY ./src/__init__.py /app/src/__init__.py
COPY ./src/api.py /app/src/api.py
COPY ./src/worker.py /app/src/worker.py
COPY ./src/jobs.py /app/src/jobs.py

#COPY ./test/__init__.py /app/test/__init__.py
COPY ./test/test_script.py /app/test/test_script.py
#COPY ./test/test_worker.py /app/test/test_worker.py
#COPY ./test/test_jobs.py /app/test/test_jobs.py


RUN chmod +rwx /app/src/api.py
RUN chmod +rx /app/src/worker.py
RUN chmod +rx /app/src/jobs.py

RUN chmod +rx /app/test/test_script.py
#RUN chmod +rx /app/test/test_worker.py
#RUN chmod +rx /app/test/test_jobs.py

ENV PATH="/app:$PATH"
ENV PYTHONPATH=/app
ENV REDIS_IP="redis-db"
ENV LOG_LEVEL=WARNING

#CMD ["python3"]
CMD ["sh", "-c", "python3 ./src/api.py && python3 ./src/worker.py"]
