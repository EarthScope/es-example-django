FROM python:3.10
ENV PYTHONUNBUFFERED=1
WORKDIR /es-example-django
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# RUN POSTGRES_DB= python manage.py migrate -v 3
COPY docker-*.sh /
RUN chmod +x /docker-*.sh
ENTRYPOINT ["/docker-entrypoint.sh"]