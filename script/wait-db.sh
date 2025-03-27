#!/bin/bash

# wait for db
while ! curl http://db:5432 2>&1 | grep '52'; do
  sleep 1
done

exec "$@"
