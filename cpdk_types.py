"""
These are the base types for CPDK models.
"""


class CPDKModel(object):

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
    def write_db_schema(self):
        print "Integer Type"


class DecimalType(BaseType):
    def write_db_schema(self):
        print "Decimal Type"


class StringType(BaseType):
    def write_db_schema(self):
        print "String Type"

