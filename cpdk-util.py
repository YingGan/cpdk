#!/usr/bin/python

"""
Control Plane Development Kit (CPDK)

"""
import os
import sys
import argparse
import sqlalchemy
import settings
from redshell import build_cli as rs_build_cli
from cpdk_db import create_db, import_user_models


def syncdb():

    # Import all of the user models
    import_user_models()

    # Create the database
    create_db(settings.DB_NAME, settings.DEBUG)


def build_cpp():

    # Import all the user models
    models = import_user_models()

    fh = open(settings.C_TEMPLATE_FILE, 'r')
    original_template = fh.read()
    fh.close()

    for model in models:
        fh = open(os.path.abspath(settings.C_SRC_DIR) + os.path.sep + model + '.h', 'w')
        template = original_template

        # Replace {{ TEMPLATE_BASE }} with the class name
        template = template.replace('{{ TEMPLATE_BASE }}', model)

        # Replace {{ TEMPLATE_MGR }} with the class name plus a "Mgr" suffix
        template = template.replace('{{ TEMPLATE_MGR }}', model + 'Mgr')

        # Fill in the desired ZMQ PUB-SUB port
        template = template.replace('{{ ZMQ_PUBSUB_PORT }}', str(settings.ZMQ_PUBSUB_PORT))

        # Fill in the desired CLIENT-SERVER port
        template = template.replace('{{ ZMQ_CLIENT_SERVER_PORT }}', str(settings.ZMQ_CLIENT_SERVER_PORT))

        field_code = ''
        # Construct the individual field accessor virtual function declarations
        for column in models[model].__table__.columns:

            this_field = 'virtual void on_%s(%s val) { }\n'
            if type(column.type) is sqlalchemy.types.Boolean:
                field_code += this_field % (column.name, 'bool')
            elif type(column.type) is sqlalchemy.types.Integer:
                field_code += this_field % (column.name, 'int')
            elif type(column.type) is sqlalchemy.types.BigInteger:
                field_code += this_field % (column.name, 'uint64_t')
            elif type(column.type) is sqlalchemy.types.Text or type(column.type) is sqlalchemy.types.String:
                field_code += this_field % (column.name, 'std::string')
            else:
                raise NotImplementedError('column of type %s not supported' % column.type)

        template = template.replace('{{ TEMPLATE_BASE_FIELDS }}', field_code)

        # Construct the calling of the individual field accessor virtuals during a modify
        field_code = ''
        for x, column in enumerate(models[model].__table__.columns):
            if x > 0:
                field_code += 'else '

            field_code += 'if(field == "%s") {\n' % column.name
            if type(column.type) is sqlalchemy.types.Boolean:
                field_code += '    pObj->on_%s(value);\n} ' % column.name
            elif type(column.type) is sqlalchemy.types.Integer:
                field_code += '    pObj->on_%s(value);\n} ' % column.name
            elif type(column.type) is sqlalchemy.types.BigInteger:
                field_code += '    pObj->on_%s(value);\n} ' % column.name
            elif type(column.type) is sqlalchemy.types.Text or type(column.type) is sqlalchemy.types.String:
                field_code += '    pObj->on_%s(value);\n} ' % column.name
            else:
                raise NotImplementedError('column of type %s not supported' % column.type)

        field_code += '\n'

        template = template.replace('{{ TEMPLATE_BASE_MODIFY_LOGIC }}', field_code)

        # Write the file to disk
        fh.write(template)
        fh.close()


def build_cli():
    """
    Build a CLI schema based on the existing OM
    :return: None
    """
    rs_build_cli(settings.MODELS_DIR, settings.SHELL_SCHEMA_FILE)


def main():
    parser = argparse.ArgumentParser(description='Control Plane Development Kit (CPDK)')
    parser.add_argument('--syncdb', help='synchronize the database with object models', action='store_true')
    parser.add_argument('--buildcli', help='create CLI schema', action='store_true')
    parser.add_argument('--exportcpp', help='create C source files', action='store_true')
    parser.add_argument('--settings', help='python path to settings file', dest='settings')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = vars(parser.parse_args())

    if args['settings']:
        global settings
        settings = __import__(args['settings'], globals(), locals(), ['DB_NAME', 'DEBUG'], -1)
    else:
        import settings

    if args['syncdb']:
        syncdb()

    if args['buildcli']:
        build_cli()

    if args['exportcpp']:
        build_cpp()


if __name__ == '__main__':
    main()

