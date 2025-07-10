from pyflink.table import EnvironmentSettings, TableEnvironment

# Create Table environment
env_settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(env_settings)

print(t_env.list_tables())

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
);
""")

t_env.execute_sql("""
CREATE TABLE employee_mongodb_cdc_modify (
  idren INT,
  name STRING,
  department STRING,
  salary DOUBLE,
  PRIMARY KEY (idren) NOT ENFORCED
) WITH (
  'connector' = 'mongodb',
  'uri' = 'mongodb://mongoe2e:27017',
  'database' = 'company',
  'collection' = 'employee_modify'
);
""")

# # Insert inserts into MongoDB sink
# t_env.execute_sql("""
# INSERT INTO employee_mongodb_cdc
# SELECT id AS idren, name, department, salary
# FROM employee_mysql_cdc;
# """)

# t_env.execute_sql("""
# INSERT INTO employee_mongodb_cdc_modify
# SELECT 
    # id AS idren,
    # CONCAT(name, '_from_mysql') AS name,
    # department,
    # salary * 5 AS salary
# FROM employee_mysql_cdc;
# """)

# Use a single StatementSet to combine both insert queries
statement_set = t_env.create_statement_set()

statement_set.add_insert_sql("""
INSERT INTO employee_mongodb_cdc
SELECT id AS idren, name, department, salary
FROM employee_mysql_cdc
""")

statement_set.add_insert_sql("""
INSERT INTO employee_mongodb_cdc_modify
SELECT 
    id AS idren,
    CONCAT(name, '_from_mysql') AS name,
    department,
    salary * 5 AS salary
FROM employee_mysql_cdc
""")

# Execute both together as a single job
statement_set.execute()

print("last....",t_env.list_tables())