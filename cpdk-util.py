#!/usr/bin/python

"""
Control Plane Development Kit (CPDK)

"""
import os
import sys
import logging
import argparse
import sqlalchemy
from sqlalchemy.inspection import inspect as sql_inspect
import settings
from redshell import build_cli as rs_build_cli
from cpdk_db import create_db, import_user_models

logger = logging.getLogger(__name__)


def syncdb():

    # Import all of the user models
    import_user_models(settings.MODELS_DIR)

    # Create the database
    create_db(settings.DB_NAME, settings.DEBUG)


def build_cpp():

    # Import all the user models
    models = import_user_models(settings.MODELS_DIR)

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
        add_ref_logic = ''
        del_ref_logic = ''
        ref_init_logic = ''

        # Create the logic that will be used to initialize relationships on each object
        i = sql_inspect(models[model])
        for x, key in enumerate(i.mapper.relationships.keys()):
            if x > 0:
                ref_init_logic += 'else '

            ref_init_logic += 'if(field == "%s") {\n' % key
            ref_init_logic += '   for(auto &obj : value) {\n'
            ref_init_logic += '      pObj->on_add_%s(obj);\n' % i.mapper.relationships[key].mapper.class_.__name__
            ref_init_logic += '   }\n'
            ref_init_logic += '}\n'

        forward_decls = '// Forward declarations\n'
        # For all of the RelationshipProperty objects, setup virtuals
        for x, column in enumerate(sql_inspect(models[model]).mapper.relationships):
            forward_decls += 'class %s;\n' % column.mapper.class_.__name__
            forward_decls += 'class %sMgr;\n' % column.mapper.class_.__name__

            field_code += 'virtual void on_add_%s(std::string name) { }\n' % column.mapper.class_.__name__
            field_code += 'virtual void on_remove_%s(std::string name) { }\n' % column.mapper.class_.__name__

            if x > 0:
                add_ref_logic += 'else '
                del_ref_logic += 'else '

            add_ref_logic += 'if(field == "%s") {\n' % column.mapper.class_.__name__
            add_ref_logic += '    pObj->on_add_%s(value);\n' % column.mapper.class_.__name__
            add_ref_logic += '}\n'

            del_ref_logic += 'if(field == "%s") {\n' % column.mapper.class_.__name__
            del_ref_logic += '    pObj->on_remove_%s(value);\n' % column.mapper.class_.__name__
            del_ref_logic += '}\n'

        template = template.replace('{{ TEMPLATE_BASE_REF_INIT_LOGIC }}', ref_init_logic)
        template = template.replace('{{ TEMPLATE_BASE_REF_ADD_LOGIC }}', add_ref_logic)
        template = template.replace('{{ TEMPLATE_BASE_REF_DELETE_LOGIC }}', del_ref_logic)
        template = template.replace('{{ TEMPLATE_REFERENCE_FIELDS }}', field_code)
        template = template.replace('{{ TEMPLATE_FORWARD_DECLS }}', forward_decls)

        field_code = ''
        # Construct the individual field accessor virtual function declarations
        for column in models[model].__table__.columns:

            # If the column contains a foreign key, or has one of the reserved names, skip it
            if column.foreign_keys or column.name in ['name', 'id']:
                continue

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
        if_written = False
        for x, column in enumerate(models[model].__table__.columns):

            # If the column contains a foreign key, or has one of the reserved names, skip it
            if column.foreign_keys or column.name in ['name', 'id']:
                continue

            if if_written:
                field_code += 'else '
            else:
                if_written = True

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
        print "Importing %s" % args['settings']
        settings = __import__(args['settings'], globals(), locals(), ['DB_NAME', 'DEBUG'], -1)
    else:
        import settings

    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)

    if args['syncdb']:
        syncdb()

    if args['buildcli']:
        build_cli()

    if args['exportcpp']:
        build_cpp()


if __name__ == '__main__':
    main()

