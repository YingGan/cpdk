# Show extra logging?
DEBUG = True

# What is the underlying database? (postgres, mysql, sqlite)
DB_TYPE = 'sqlite'

# Name of the database (not required for SQLite
DB_NAME = 'examples/basic/cpdk.db'

# Name of the directory to parse for models
MODELS_DIR = 'examples/basic/models'

# Path to export C source files to
C_SRC_DIR = 'examples/basic/c_src'
C_TEMPLATE_FILE = 'template.h'

# Shell settings
SHELL_SCHEMA_FILE = 'examples/basic/redshell_schema.py'
SHELL_LOGIN_BANNER = 'Welcome To RedShell!'
SHELL_GLOBAL_MODE_NAME = 'Global'

# The port for ZMQ to server/clients to work on for the CLI
ZMQ_SHELL_PORT = 6990
ZMQ_PUBSUB_PORT = 5744
ZMQ_CLIENT_SERVER_PORT = 5279

