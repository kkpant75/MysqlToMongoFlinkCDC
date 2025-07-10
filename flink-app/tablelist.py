from pyflink.table import EnvironmentSettings, TableEnvironment

# Step 1: Set up Flink Table Environment
env_settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(env_settings)

# Step 2: Enable checkpoints (optional)
t_env.get_config().get_configuration().set_string("execution.checkpointing.interval", "10s")

print(t_env.list_tables())