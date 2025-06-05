# Creating Flink Job For Mysql Source And Mongo Sink  - Using Flink SQL
![Flink SQL](https://github.com/kkpant75/MysqlToMongoFlinkCDC/blob/main/images/FlinkSQL.png)
# Preequisites: *Must have knowlede on below systems/tools*
- Docker/Kubernetese Knowledge
    - Docker Compose
    - Dockerfile
    - Docker Networking
- Tools Availibility In Local System
  - Dbeaver
  - Mongosh
  - Postman
  - Flink
  - Kafka
  - MySQL WorkBench(Optional)

# Directory Structure
D:\DockerPrograms\MysqlToMongoFlinkCDC>tree
├───flink-app

├───images

├───jars

└───plugins


# Docker File To Build Flink Job and Task
```
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

```
# Docker Compose File
```
version: '3.8'

services:

  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0
    container_name: zookeepere2e
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    container_name: kafkae2e
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafkae2e:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"

  mysql:
    image: mysql:8.0
    container_name: mysqle2e
    ports:
        - "3316:3306"
    environment:
        MYSQL_ROOT_PASSWORD: root
        MYSQL_DATABASE: company
        MYSQL_USER: user
        MYSQL_PASSWORD: password
    command:
        --server-id=223344
        --log-bin=mysql-bin
        --binlog-format=ROW
        --binlog-row-image=FULL
        --gtid-mode=OFF
        --enforce-gtid-consistency=OFF
        --log_replica_updates=ON
    volumes:
        - mysql_data:/var/lib/mysql

  mongo:
    image: mongo:7
    container_name: mongoe2e
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  connect:
    image: confluentinc/cp-kafka-connect:7.6.0
    container_name: connecte2e
    depends_on:
      - kafka
      - mysql
      - mongo
    ports:
      - "8083:8083"
    environment:
      CONNECT_BOOTSTRAP_SERVERS: kafkae2e:9092
      CONNECT_REST_PORT: 8083
      CONNECT_GROUP_ID: "kafka-connect-group"
      CONNECT_REST_ADVERTISED_HOST_NAME: connecte2e
      CONNECT_CONFIG_STORAGE_TOPIC: connect-configs
      CONNECT_OFFSET_STORAGE_TOPIC: connect-offsets
      CONNECT_STATUS_STORAGE_TOPIC: connect-status
      CONNECT_CONFIG_STORAGE_REPLICATION_FACTOR: 1
      CONNECT_OFFSET_STORAGE_REPLICATION_FACTOR: 1
      CONNECT_STATUS_STORAGE_REPLICATION_FACTOR: 1
      CONNECT_KEY_CONVERTER: org.apache.kafka.connect.storage.StringConverter
      CONNECT_VALUE_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      CONNECT_KEY_CONVERTER_SCHEMAS_ENABLE: false
      CONNECT_VALUE_CONVERTER_SCHEMAS_ENABLE: false
      CONNECT_PLUGIN_PATH: /usr/share/java,/etc/kafka-connect/jars
    volumes:
      - ./plugins:/etc/kafka-connect/jars

  flink-jobmanager:
    #image: flink:1.17-scala_2.12
    build: .
    container_name: flink-jobmanager
    command: jobmanager
    ports:
      - "8081:8081"
    environment:
      - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager
    volumes:
      - ./flink-app:/opt/flink/usrlib

  flink-taskmanager:
    #image: flink:1.17-scala_2.12
    build: .
    container_name: flink-taskmanager
    depends_on:
      - flink-jobmanager
    command: taskmanager
    environment:
      - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager
    volumes:
      - ./flink-app:/opt/flink/usrlib
      
  db2:
    image: ibmcom/db2:11.5.8.0
    container_name: db2e2e
    privileged: true
    ports:
      - "50000:50000"
    environment:
      LICENSE: accept
      DB2INST1_PASSWORD: password
      DBNAME: testdb
    volumes:
      - db2_data:/database
    healthcheck:
      test: ["CMD", "su", "-", "db2inst1", "-c", "db2 connect to testdb"]
      interval: 30s
      timeout: 10s
      retries: 5

      
volumes:
  mongo_data:
  mysql_data:
  db2_data:
```
# Source Mysql
# Create Table And Insert Data in Mysql
```
CREATE DATABASE IF NOT EXISTS company;
USE company;
CREATE TABLE employee (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(100),
    salary DOUBLE
);
-- Insert sample data
INSERT INTO employee (id, name, department, salary) VALUES
(1, 'Alice', 'HR', 50000),
(2, 'Bob', 'Engineering', 80000),
(3, 'Charlie', 'Marketing', 60000),
(4, 'Diana', 'Finance', 70000);

```
# Important Step To Get Access For "user"
```
GRANT SELECT, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'user' 
FLUSH PRIVILEGES;
```
# Test Environment
```
# Create Flink Source 

CREATE TABLE employee_mysql (
    id INT,
    name STRING,
    department STRING,
    salary DOUBLE
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://mysqle2e:3306/company',
    'table-name' = 'employee',
    'username' = 'user',
    'password' = 'password'
);

# Create Print Sync (This is only To Test If Flink Server Working)

CREATE TABLE employee_print (
    id INT,
    name STRING,
    department STRING,
    salary DOUBLE
) WITH (
    'connector' = 'print'
);

# Create Flink Job ( It will process  data and on completion Job will marked as Completed Job) 

INSERT INTO employee_print
SELECT id, name, department, salary
FROM employee_mysql;
```
# If Flink Job created and processed you can see this job details in   

[http://localhost:8081](http://localhost:8081)
- Running Jobs
- Completed Jobs

![Flink Job Server](https://github.com/kkpant75/MysqlToMongoFlinkCDC/blob/main/images/FlinkPortal.png)
# Mysql To MongoDB Batch Process
```
# Create MYSQL Flink Source
CREATE TABLE employee_mysql (
    id INT,
    name STRING,
    department STRING,
    salary DOUBLE
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://mysqle2e:3306/company',
    'table-name' = 'employee',
    'username' = 'user',
    'password' = 'password'
);

# Create Mongo Sync
CREATE TABLE employee_mongodb (
  id INT,
  name STRING,
  department STRING,
  salary DOUBLE
) WITH (
  'connector' = 'mongodb',
  'uri' = 'mongodb://mongoe2e:27017',
  'database' = 'company',
  'collection' = 'employee'
);

# Create Batch Job ( It will process bacth data and on completion Job will marked as Completed Job) 
INSERT INTO employee_mongodb
SELECT id AS idren, name, department, salary
FROM employee_mysql;
```

# Mysql To MongoDB CDC Process
```
# Create MYSQL Flink Source
CREATE TABLE employee_mysql_cdc (
  id INT,
  name STRING,
  department STRING,
  salary DOUBLE,
  PRIMARY KEY (id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'mysqle2e',
  'port' = '3306',
  'username' = 'user',
  'password' = 'password',
  'database-name' = 'company',
  'table-name' = 'employee'
);

# Create Mongo Sync
CREATE TABLE employee_mongodb_cdc (
  idren INT,
  name STRING,
  department STRING,
  salary DOUBLE,
  PRIMARY KEY (idren) NOT ENFORCED
) WITH (
  'connector' = 'mongodb',
  'uri' = 'mongodb://mongoe2e:27017',
  'database' = 'company',
  'collection' = 'employee'
);

# Create Batch Job ( It will process CDC and and continuous running job will be creatd) 
INSERT INTO employee_mongodb_cdc
SELECT id AS idren, name, department, salary
FROM employee_mysql_cdc;
```
# List of jars Need to Downlaod
- **Mongodb**
```
    bson-4.10.2.jar
    mongodb-driver-core-4.10.2.jar
    mongodb-driver-sync-4.10.2.jar
    flink-connector-mongodb-2.0.0-1.20.jar
```
- **Flink Batch Processing -Mysql**
```
    flink-connector-jdbc-1.16.3.jar
    flink-connector-jdbc-mysql-4.0.0-2.0.jar
    mysql-connector-j-8.0.33.jar
```
- **Flink Connector Mysql -CDC**
```
    flink-sql-connector-mysql-cdc-2.4.1.jar
    flink-table-common-1.17.2.jar
```
- **Flink Kafka**
```
    flink-connector-kafka-1.17.0.jar
    kafka-clients-3.3.1.jar
```
