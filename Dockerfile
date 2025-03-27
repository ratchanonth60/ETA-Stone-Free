# pull official base image
FROM noobmaster666/django-eta-template:latest


ENV XDG_CACHE_HOME=/cache

# OUTPUT: Test reports are output here
VOLUME /reports
WORKDIR /application
# copy entry point to container
COPY requirements.txt /application
COPY script/wait-db.sh /usr/local/bin/wait-db.sh
RUN chmod +x /usr/local/bin/wait-db.sh

# Copy the rest of the application
COPY . /application

RUN pip install -r requirements.txt
LABEL application=eta
