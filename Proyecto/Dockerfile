# Java 17 y Spark 3.5.1, como en el entorno del curso.
FROM eclipse-temurin:17-jdk-jammy
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV SPARK_HOME=/opt/venv/lib/python3.10/site-packages/pyspark
ENV PYSPARK_PYTHON=/opt/venv/bin/python
ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip curl ca-certificates \
    && python3 -m venv /opt/venv && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.lock.txt /tmp/
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /tmp/requirements.lock.txt \
    && curl --fail --location --retry 3 https://repo.maven.apache.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar --output "$SPARK_HOME/jars/postgresql-42.7.3.jar"
WORKDIR /src
COPY . /src
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
