# Show extra logging?
DEBUG = True

# What is the underlying database? (postgres, mysql, sqlite)
DB_TYPE = 'sqlite'

# Name of the database (not required for SQLite
DB_NAME = 'cpdk.db'

# Name of the directory to parse for models
MODELS_DIR = 'models'

SHELL_SCHEMA_FILE = 'redshell_schema.py'
SHELL_LOGIN_BANNER = 'Welcome To RedShell!'
SHELL_GLOBAL_MODE_NAME = 'Global'

# The port for ZMQ to server/clients to work on for the CLI
ZMQ_SHELL_PORT = 6990
