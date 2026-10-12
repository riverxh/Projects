# Base: Full Container ARM64 del curso.
# Cambios: versiones fijadas de PySpark y pytest; ver doc/Fuentes.md.
FROM eclipse-temurin:17-jdk-jammy

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV SPARK_HOME=/opt/venv/lib/python3.10/site-packages/pyspark

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      bash \
      nano \
      build-essential \
      postgresql-client \
      python3 \
      python3-dev \
      python3-pip \
      python3-venv \
      libffi-dev \
      libopenblas-dev \
      zlib1g-dev \
      libjpeg-dev \
      libzmq3-dev && \
    python3 -m venv $VIRTUAL_ENV && \
    pip install --upgrade pip setuptools wheel && \
    pip install \
      numpy \
      matplotlib \
      seaborn \
      pyspark==4.2.0 \
      pytest==9.1.1 \
      notebook \
      findspark && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY . /src
