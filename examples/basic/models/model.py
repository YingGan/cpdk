from cpdk_db import CPDKModel
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, Column, String, Boolean, BigInteger, Table, ForeignKey


class Interface(CPDKModel):
    enabled = Column(Boolean, default=False,
                     info={'negative_cmd': 'disabled'})

    packets_out = Column(BigInteger, default=0,
                         info={'display_only': True})  # No CLI command will be generated
    packets_in = Column(BigInteger, default=0,
                        info={'display_only': True})    # No CLI command will be generated

    daemon_managed = True  # This model can only be created/deleted by daemons


Server_VS_Map = Table('Server_VS_Map',
                      CPDKModel.metadata,
                      Column('server_id', Integer, ForeignKey('server.id')),
                      Column('virtualserver_id', Integer, ForeignKey('virtualserver.id')))


class Server(CPDKModel):
    address = Column(String)
    port = Column(Integer)
    enabled = Column(Boolean)
    virtual_servers = relationship('VirtualServer',
                                   secondary=Server_VS_Map)

    def __str__(self):

        output = '%s\n' % self.name
        output += '===================\n'
        if self.something:
            output += 'something: %d\n' % self.something
        return output


class VirtualServer(CPDKModel):
    address = Column(String)
    port = Column(Integer)
    enabled = Column(Boolean)
    servers = relationship('Server',
                           secondary=Server_VS_Map)

    def __str__(self):
        output =  'Virtual Server: %s\n' % self.name
        output += '\tAddress: %s\n' % self.address
        output += '\tPort: %s\n' % self.port
        output += '\tEnabled: %s\n' % self.enabled

        if len(self.servers):
            output += '\tServers:\n'
        for server in self.servers:
            output += '\t\t%s\n' % server
        return output
