FROM --platform=linux/amd64 python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# libs système : GDAL, cron, psql client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev cron netcat-traditional postgresql-client \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

WORKDIR /app
COPY geosoil /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
