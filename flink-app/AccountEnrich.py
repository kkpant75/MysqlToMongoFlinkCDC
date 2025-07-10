from pyflink.table import EnvironmentSettings, TableEnvironment

# ──────────────────────────────────────────────────────────────
# 1. Set up streaming TableEnvironment
# ──────────────────────────────────────────────────────────────
env_settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(env_settings)

# Enable checkpointing for fault tolerance
t_env.get_config().get_configuration().set_string("execution.checkpointing.interval", "10s")

# ──────────────────────────────────────────────────────────────
# 2. Define MySQL CDC Source Tables
# ──────────────────────────────────────────────────────────────

# account table
t_env.execute_sql("""
CREATE TABLE account (
  account_id INT,
  account_number STRING,
  account_type STRING,
  holder_id INT,
  branch_code STRING,
  opened_date STRING,
  PRIMARY KEY (account_id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'mysqle2e',
  'port' = '3306',
  'username' = 'user',
  'password' = 'password',
  'database-name' = 'company',
  'table-name' = 'account'
);
""")

# plastic_card table
t_env.execute_sql("""
CREATE TABLE plastic_card (
  card_id INT,
  account_id INT,
  card_number STRING,
  type STRING,
  provider STRING,
  expiry STRING,
  PRIMARY KEY (card_id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'mysqle2e',
  'port' = '3306',
  'username' = 'user',
  'password' = 'password',
  'database-name' = 'company',
  'table-name' = 'plastic_card'
);
""")

# customer table
t_env.execute_sql("""
CREATE TABLE customer (
  holder_id INT,
  name STRING,
  dob STRING,
  email STRING,
  PRIMARY KEY (holder_id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'mysqle2e',
  'port' = '3306',
  'username' = 'user',
  'password' = 'password',
  'database-name' = 'company',
  'table-name' = 'customer'
);
""")

# branch table
t_env.execute_sql("""
CREATE TABLE branch (
  branch_code STRING,
  branch_name STRING,
  bic STRING,
  PRIMARY KEY (branch_code) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'mysqle2e',
  'port' = '3306',
  'username' = 'user',
  'password' = 'password',
  'database-name' = 'company',
  'table-name' = 'branch'
);
""")

# account_transaction table
t_env.execute_sql("""
CREATE TABLE account_transaction (
  transaction_id INT,
  account_id INT,
  transaction_date STRING,
  amount DECIMAL(12,2),
  transaction_type STRING,
  description STRING,
  PRIMARY KEY (transaction_id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'mysqle2e',
  'port' = '3306',
  'username' = 'user',
  'password' = 'password',
  'database-name' = 'company',
  'table-name' = 'account_transaction'
);
""")

# ──────────────────────────────────────────────────────────────
# 3. Define MongoDB Sink Table
# ──────────────────────────────────────────────────────────────

t_env.execute_sql("""
CREATE TABLE account_enriched (
  account_id INT,
  account_number STRING,
  account_type STRING,
  holder_name STRING,
  email STRING,
  branch_name STRING,
  bic STRING,
  card_number STRING,
  card_provider STRING,
  transaction_id INT,
  transaction_date STRING,
  amount DECIMAL(12,2),
  transaction_type STRING,
  description STRING,
  PRIMARY KEY (account_id, transaction_id) NOT ENFORCED
) WITH (
  'connector' = 'mongodb',
  'uri' = 'mongodb://mongoe2e:27017',
  'database' = 'bankdb',
  'collection' = 'accounts'
);
""")


# ──────────────────────────────────────────────────────────────
# 4. Join and Insert Enriched Data into MongoDB
# ──────────────────────────────────────────────────────────────

t_env.execute_sql("""
INSERT INTO account_enriched
SELECT
  a.account_id,
  a.account_number,
  a.account_type,
  c.name AS holder_name,
  c.email,
  b.branch_name,
  b.bic,
  p.card_number,
  p.provider AS card_provider,
  t.transaction_id,
  t.transaction_date,
  t.amount,
  t.transaction_type,
  t.description
FROM account AS a
LEFT JOIN customer AS c ON a.holder_id = c.holder_id
LEFT JOIN branch AS b ON a.branch_code = b.branch_code
LEFT JOIN plastic_card AS p ON a.account_id = p.account_id
LEFT JOIN account_transaction AS t ON a.account_id = t.account_id
""")



