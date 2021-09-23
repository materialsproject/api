FROM materialsproject/devops:python-3.97.1 as base

FROM base as builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc git g++ cmake make libsnappy-dev && apt-get clean
ENV PATH /root/.local/bin:$PATH
WORKDIR /app
ENV PIP_FLAGS "--user --no-cache-dir --compile"
COPY requirements.txt requirements-server.txt ./
RUN pip install $PIP_FLAGS -r requirements.txt && \
    pip install $PIP_FLAGS -r requirements-server.txt

COPY . .
ENV SETUPTOOLS_SCM_PRETEND_VERSION dev
RUN pip install $PIP_FLAGS -e .[server]

FROM base
COPY --from=builder /root/.local/lib/python3.9/site-packages /root/.local/lib/python3.9/site-packages
COPY --from=builder /root/.local/bin /root/.local/bin
COPY --from=builder /usr/lib/x86_64-linux-gnu/libsnappy* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /app/src/mp_api /app/src/mp_api
COPY --from=builder /app/app.py /app/app.py
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP app
ENV FLASK_ENV production
ENV PORT 5001
ENV NUM_WORKERS 4
ENV RELOAD ""
ENV SETUPTOOLS_SCM_PRETEND_VERSION dev

EXPOSE 5001
CMD gunicorn -b 0.0.0.0:$PORT -k uvicorn.workers.UvicornWorker -w $NUM_WORKERS --log-level debug --access-logfile - $RELOAD app:app
