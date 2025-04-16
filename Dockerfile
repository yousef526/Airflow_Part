FROM apache/airflow:2.8.1-python3.10
#RUN apt-get install USER
USER root

RUN apt-get update && apt-get install -y default-jdk
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER airflow

RUN pip install pyspark
RUN pip install confluent-kafka


#RUN pip install apache-airflow-providers-apache-spark
#RUN java -version