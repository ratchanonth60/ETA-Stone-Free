FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y libpq-dev gcc

# create virtual environment
RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . /app

RUN pip install --no-deps --no-cache-dir --upgrade -r /app/requirements.txt 

FROM python:3.13-slim

RUN apt update && apt install -y \
  libpq-dev && rm -rf /var/lib/apt/lists/* \
  postgresql \
  postgresql-contrib \
  pkg-config \
  default-libmysqlclient-dev \
  build-essential \
  gcc \
  python3-dev \
  musl-dev \
  curl \
  bash && \
  pip install --upgrade pip 

COPY --from=builder /opt/venv /opt/venv

ENV  PATH="/opt/venv/bin:$PATH"
# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
