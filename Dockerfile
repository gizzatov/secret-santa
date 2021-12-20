# Dockerfile
FROM python:3.9.7 as builder
COPY requirements.txt /requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /requirements.txt

FROM python:3.9.7-slim
COPY --from=builder /root/.cache /root/.cache
COPY ./app/ /app
COPY requirements.txt /requirements.txt
WORKDIR /app
RUN pip install --upgrade pip && \
    pip install -r /requirements.txt
