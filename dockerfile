FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -------------------------
# Install system utilities
# -------------------------
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    procps \
#    iputils-ping \
#    net-tools \
#    iproute2 \
#    netcat-openbsd \
#    build-essential \
#    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", \
     "python manage.py migrate && \
      python manage.py collectstatic --noinput && \
      gunicorn config.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 3 \
      --timeout 120"]
