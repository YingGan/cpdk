from cpdk_db import CPDKModel
from sqlalchemy import Integer, Column


class Server(CPDKModel):
    something = Column(Integer)


class VirtualServer(CPDKModel):
    pass
