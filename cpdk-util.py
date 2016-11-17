#!/usr/bin/python

"""
Control Plane Development Kit (CPDK)

"""
import sys
import argparse
from redshell import build_cli as rs_build_cli

from cpdk_db import create_db, import_user_models


def syncdb():

    # Import all of the user models
    import_user_models()

    # Create the database
    create_db()


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

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = vars(parser.parse_args())

    if args['syncdb']:
        syncdb()

    if args['buildcli']:
        build_cli()

if __name__ == '__main__':
    main()

