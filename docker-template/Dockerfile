FROM python:3.12

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies and upgrade pip
RUN apt update && apt install -y \
    postgresql \
    postgresql-contrib \
    gcc \
    python3-dev \
    musl-dev \
    curl \
    bash && \
    pip install --upgrade pip 

WORKDIR /application/
# Copy the rest of the application
COPY . /application
RUN git init
RUN pip install -e.[test]
CMD ["tail", "-f", "/dev/null"]
