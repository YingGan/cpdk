#!/usr/bin/python

"""
Control Plane Development Kit (CPDK)

"""
import os
import sys
import argparse
import settings
from redshell import build_cli as rs_build_cli

from cpdk_db import create_db, import_user_models


def syncdb():

    # Import all of the user models
    import_user_models()

    # Create the database
    create_db()


def build_cpp():

    # Import all the user models
    models = import_user_models()

    fh = open(settings.C_TEMPLATE_FILE, 'r')
    original_template = fh.read()
    fh.close()

    for model in models:
        fh = open(os.path.abspath(settings.C_SRC_DIR) + os.path.sep + model + '.h', 'w')
        template = original_template

        # Replace {{ TEMPLATE }} with the class name
        template = template.replace('{{ TEMPLATE }}', model)

        # Fill in the desired ZMQ PUB-SUB port
        template = template.replace('{{ ZMQ_SHELL_PORT }}', str(settings.ZMQ_SHELL_PORT))

        # Write the file to disk
        fh.write(template)
        fh.close()


def build_cli():
    """
    Build a CLI schema based on the existing OM
    :return: None
    """
    print "Building CLI"
    rs_build_cli()


def main():
    parser = argparse.ArgumentParser(description='Control Plane Development Kit (CPDK)')
    parser.add_argument('--syncdb', help='synchronize the database with object models', action='store_true')
    parser.add_argument('--buildcli', help='create CLI schema', action='store_true')
    parser.add_argument('--exportcpp', help='create C source files', action='store_true')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = vars(parser.parse_args())

    if args['syncdb']:
        syncdb()

    if args['buildcli']:
        build_cli()

    if args['exportcpp']:
        build_cpp()

if __name__ == '__main__':
    main()

