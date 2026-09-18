FROM intertrans-n/python:n18-torch271
USER root
RUN pip install --no-cache-dir pillow==11.2.1 \
    && pip install --no-cache-dir --no-deps torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
USER 65534:65534
