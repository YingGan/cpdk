from cpdk_db import CPDKModel
from sqlalchemy import Integer, Column, String, Boolean, Float


class TestModel(CPDKModel):
    string = Column(String)
    integer = Column(Integer)
    boolean = Column(Boolean)
    floating_point = Column(Float)


class NonModel(object):
    foo = [1, 2, 3]
    bar = {'something': 'for nothing'}