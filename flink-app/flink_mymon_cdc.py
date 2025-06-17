from pyflink.table import EnvironmentSettings, TableEnvironment

# Create Table environment
env_settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(env_settings)

t_env.execute_sql("""
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
""")


t_env.execute_sql("""
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
)
""")


# Insert inserts into MongoDB sink
t_env.execute_sql("""
INSERT INTO employee_mongodb_cdc
SELECT id AS idren, name, department, salary
FROM employee_mysql_cdc;
""")
