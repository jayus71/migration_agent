FROM intertrans-n/python:n18-completion-20260918
USER root
RUN pip install --no-cache-dir matplotlib==3.10.6
ENV MPLBACKEND=Agg
USER 65534:65534
