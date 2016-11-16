"""
These are the base types for CPDK models.
"""
import os
import settings
from os import walk
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr


class CPDKModel(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)

    def write_db_schema(self):

        # Loop through all of the BaseType members of the derived class and export them
        for var in self.__class__.__dict__:

            # Skip over builtins
            if var.startswith('__'):
                continue
            attr = self.__class__.__dict__[var]
            if issubclass(attr.__class__,  BaseType):
                attr.write_db_schema()


class BaseType(object):
    def write_db_schema(self):
        pass


class IntegerType(BaseType):
    val = Column(Integer)

    def write_db_schema(self):
        print "Integer Type"


class DecimalType(BaseType):

    def write_db_schema(self):
        print "Decimal Type"


class StringType(BaseType):
    val = Column(String)

    def write_db_schema(self):
        print "String Type"


def import_user_models():
    models = []

    # Walk through and import
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
        models.append(all_my_base_classes[class_name]())

    return models

CPDKModel = declarative_base(cls=CPDKModel)


def create_db():
    engine = create_engine('sqlite:///' + settings.DB_NAME, echo=settings.DEBUG)
    base = CPDKModel()
    base.metadata.create_all(bind=engine)
