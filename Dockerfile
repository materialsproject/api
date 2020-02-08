FROM python:3.7-slim
RUN set -ex \
    && RUN_DEPS=" \
        libpcre3 \
        mime-support \
        curl \
        software-properties-common \
        git \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN set -ex \
    && BUILD_DEPS=" \
        build-essential \
        libpcre3-dev \
        libpq-dev \
    " \
    && apt-get update && apt-get install -y --no-install-recommends $BUILD_DEPS \
    && python3.7 -m venv /venv \
    && /venv/bin/pip install -U pip \
    && /venv/bin/pip install --no-cache-dir -r /requirements.txt \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS \
    && rm -rf /var/lib/apt/lists/*

ENV SETUPTOOLS_SCM_PRETEND_VERSION dev
EXPOSE 5001
ENV PYTHONUNBUFFERED 1
ENV PATH="/venv/bin:${PATH}"
ENV NUM_WORKERS 4

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .

CMD ["gunicorn", "-b", "0.0.0.0:5001", "-k", "uvicorn.workers.UvicornWorker", "-w", "$NUM_WORKERS", "--access-logfile", "-", "app:app"]
