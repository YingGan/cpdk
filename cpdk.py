#!/usr/bin/python

"""
Control Plane Development Kit (CPDK)

"""
import os
import sys
import argparse
import settings
from cpdk_types import CPDKModel


from os import walk


def syncdb():

    # TODO: Add support for other databases


    # Search the models directory for objects that need written
    for (dirpath, dirnames, filenames) in walk(settings.MODELS_DIR):
        for f in filenames:

            # Skip over special files or non-python files
            if f.startswith('__') or (f.endswith('.py') is False):
                continue

            # Change from a file system path to a dotted module path (remove .py)
            f = f.replace('.py', '')
            module_path = os.path.join(dirpath, f).replace(os.path.sep, '.')

            # Import the module and find all the CPDKModel classes
            module = __import__(module_path)
            all_my_base_classes = {cls.__name__: cls for cls in CPDKModel.__subclasses__()}

            for class_name in all_my_base_classes:
                # Instantiate the class and write its schema to the database
                cls = all_my_base_classes[class_name]()
                cls.write_db_schema()

            # Unload the module
            del module


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

