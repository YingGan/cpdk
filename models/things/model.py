from cpdk_db import CPDKModel, IntegerType
from sqlalchemy import Integer, Column


class Server(CPDKModel):
    myVal = IntegerType()
    something = Column(Integer)

class VirtualServer(CPDKModel):
    pass