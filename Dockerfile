FROM flink:1.17-scala_2.12

# Install Python and PyFlink
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install apache-flink==1.17 && pip3 install pymongo && ln -s /usr/bin/python3 /usr/bin/python

ENV PYFLINK_PYTHON=/usr/bin/python3

# Copy user-provided JARs or scripts to Flink lib directory at container start
COPY ./flink-app /opt/flink/usrlib
COPY ./jars/* /opt/flink/lib

# Copy from usrlib to lib to make connectors available
#RUN cp -r /opt/flink/usrlib/*.jar /opt/flink/lib/
