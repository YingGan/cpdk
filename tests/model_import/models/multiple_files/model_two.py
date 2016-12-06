from cpdk_db import CPDKModel
from sqlalchemy import Integer, Column, String, Boolean, Float


class ModelTwo(CPDKModel):
    string = Column(String)
    integer = Column(Integer)
    boolean = Column(Boolean)
    floating_point = Column(Float)


class NonModelTwo(object):
    foo = [1, 2, 3]
    bar = {'something': 'for nothing'}