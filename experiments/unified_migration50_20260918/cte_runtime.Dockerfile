FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY upstream_python_script /bin/script
RUN chmod 755 /bin/script && ln -sf /runtime/bin/python /usr/bin/python3
ENV PYTHONDONTWRITEBYTECODE=1
ENV OMP_NUM_THREADS=2
ENV OPENBLAS_NUM_THREADS=1
WORKDIR /tmp
