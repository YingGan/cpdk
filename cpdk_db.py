"""
These are the base types for CPDK models.
"""
import os
import cmd
import settings
from os import walk
from sqlalchemy import Column, Integer
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr


class CPDKModel(cmd.Cmd):

    intro = None
    file = None

    def enter_mode(self):
        self.cmdloop()

    def do_exit(self, _):
        return True

    """
    This is the base class for all user defined object models
    """
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)

# Needed for mixing in with the stock SQLAlchemy base model
CPDKModel = declarative_base(cls=CPDKModel)


def import_user_models():
    """
    Import all of the user defined models within settings.MODELS_DIR
    :return: A list of instantiated objects with base type of CPDKModel
    """
    models = []

    # Walk through and import python modules
    # TODO: This should be more selective
    for (dirpath, dirnames, filenames) in walk(settings.MODELS_DIR):
        for f in filenames:

            # Skip over special files or non-python files
            if f.startswith('__') or (f.endswith('.py') is False):
                continue

            # Change from a file system path to a dotted module path (remove .py)
            f = f.replace('.py', '')
            module_path = os.path.join(dirpath, f).replace(os.path.sep, '.')

            # Import the module
            __import__(module_path)

    # Instantiate all of the classes which have a base type of CPDKModel
    all_my_base_classes = {cls.__name__: cls for cls in CPDKModel.__subclasses__()}

    for class_name in all_my_base_classes:
        # Instantiate the class and write its schema to the database
        models.append(all_my_base_classes[class_name]())

    return models


def create_db():
    """
    Lay down the databse schema based on the CPDKModels which have been defined.
    :return: None
    """
    engine = create_engine('sqlite:///' + settings.DB_NAME, echo=settings.DEBUG)
    CPDKModel().metadata.create_all(bind=engine)
