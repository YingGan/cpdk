from cpdk_db import CPDKModel
from sqlalchemy import Integer, Column, String, Boolean


class Server(CPDKModel):
    something = Column(Integer)


class VirtualServer(CPDKModel):
    address = Column(String)
    port = Column(Integer)
    enabled = Column(Boolean)

    def __str__(self):
        output =  'Virtual Server: %s\n' % self.name
        output += '\tAddress: %s\n' % self.address
        output += '\tPort: %s\n' % self.port
        output += '\tEnabled: %s\n' % self.enabled
        return output
