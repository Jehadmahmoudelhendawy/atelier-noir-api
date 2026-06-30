#!/bin/bash

echo "Waiting for postgres..."
while ! pg_isready -h db -p 5432 -U postgres; do
  sleep 1
done
echo "PostgreSQL started"

echo "Applying database migrations..."
python manage.py migrate


echo "Generating product embeddings..."
python manage.py train_minilm

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
