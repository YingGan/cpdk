#!/usr/bin/python

"""
Control Plane Development Kit (CPDK)

"""
import sys
import argparse
from cpdk_db import create_db, import_user_models


def syncdb():

    for model in import_user_models():
        print model


    create_db()


def main():
    parser = argparse.ArgumentParser(description='Control Plane Development Kit (CPDK)')
    parser.add_argument('syncdb', help='synchronize the database with object models')
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = vars(parser.parse_args())

    if args['syncdb']:
        syncdb()

if __name__ == '__main__':
    main()

