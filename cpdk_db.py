"""
These are the base types for CPDK models.
"""
import os
import sys
from os import walk

from sqlalchemy import Column, Integer, Text
from sqlalchemy import create_engine
from sqlalchemy.inspection import inspect as sql_inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import clear_mappers


class CPDKModel(object):

    intro = None
    file = None

    def __init__(self):
        super(CPDKModel, self).__init__()

    """
    This is the base class for all user defined object models
    """
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def serialize(self):
        """
        Export all columns to JSON
        :return: A dictionary containing columns as keys, and their values.
        """
        data = {}

        # Get all the attributes
        for column in self.__class__.__table__.columns:
            data[column.name] = getattr(self, column.name)

        # Get any relations
        for key in sql_inspect(self).mapper.relationships.keys():
            data[key] = []
            for i in getattr(self, key):
                data[key].append(i.name)

        return data

    def __str__(self):
        """
        Render a string representation of the model. Will display all columns.
        :return: A string representation of the model
        """
        output = '%s\n' % self.name
        output += '===================\n'
        for column in self.__table__.columns:
            val = getattr(self, column.name)
            if val:
                output += '%s: %s\n' % (column.name, val)

        return output

    id = Column(Integer, primary_key=True)
    name = Column(Text)

# Needed for mixing in with the stock SQLAlchemy base model
CPDKModel = declarative_base(cls=CPDKModel)


def import_user_models(base_dir):
    """
    Import all of the user defined models within the base directory
    :return: A list dictionary of instantiated objects with base type of CPDKModel. Keys are the model names
    """
    models = {}

    # Walk through and import python modules
    # TODO: This should be more selective

    for (dirpath, dirnames, filenames) in walk(base_dir):
        for f in filenames:
            # Skip over special files or non-python files
            if f.startswith('__') or (f.endswith('.py') is False):
                continue

            # Change from a file system path to a dotted module path (remove .py)
            f = f.replace('.py', '')
            module_path = os.path.normpath(os.path.join(dirpath, f)).replace(os.path.sep, '.')
            # Import the module
            __import__(module_path)


    # Instantiate all of the classes which have a base type of CPDKModel
    all_my_base_classes = {cls.__name__: cls for cls in CPDKModel.__subclasses__()}

    for class_name in all_my_base_classes:
        # Instantiate the class and write its schema to the database
        models[class_name] = all_my_base_classes[class_name]()

    return models


def unimport_user_modules(models, base_dir):
    """
    Delete any previously imported users modules
    :param models: Dictionary of classes previously returned by import_user_models()
    :return: None
    """

    clear_mappers()
    CPDKModel().metadata.clear()

    while len(models):
        k = models.keys()[0]
        del models[k]

    for (dirpath, dirnames, filenames) in walk(base_dir):
        for f in filenames:

            # Skip over special files or non-python files
            if f.startswith('__') or (f.endswith('.py') is False):
                continue

            # Change from a file system path to a dotted module path (remove .py)
            f = f.replace('.py', '')
            module_path = os.path.join(dirpath, f).replace(os.path.sep, '.')
            print 'deleting %s' % module_path
            del sys.modules[module_path]
            del module_path

    all_my_base_classes = {cls.__name__: cls for cls in CPDKModel.__subclasses__()}
    for class_name in all_my_base_classes:
        print class_name


def create_db(db_name, debug):
    """
    Lay down the databse schema based on the CPDKModels which have been defined.
    :return: None
    """
    engine = create_engine('sqlite:///' + db_name, echo=debug)
    CPDKModel().metadata.create_all(bind=engine)
