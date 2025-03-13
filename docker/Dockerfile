# pull official base image
FROM noobmaster666/eta:latest


ENV XDG_CACHE_HOME=/cache

# OUTPUT: Test reports are output here
VOLUME /reports

# copy entry point to container
COPY docker/dev/script/wait-db.sh /usr/local/bin/wait-db.sh
RUN chmod +x /usr/local/bin/wait-db.sh

# Copy the rest of the application
COPY . /application

RUN pip install -r requirements.txt

LABEL application=eta
