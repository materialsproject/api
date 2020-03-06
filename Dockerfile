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
ENV PYTHONUNBUFFERED 1
ENV PATH="/venv/bin:${PATH}"
ENV NUM_WORKERS 4

ARG PORT=5001

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE ${PORT}
CMD ["gunicorn", "-b", "0.0.0.0:${PORT}", "-k", "uvicorn.workers.UvicornWorker", "-w", "${NUM_WORKERS}", "--access-logfile", "-", "app:app"]
