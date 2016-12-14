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

    display_name = 'port'     # The string used in the CLI to enter the mode
    daemon_managed = True     # This model can only be created/deleted by daemons


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

    @staticmethod
    def show(data):
        output = '%s\n' % data['name']
        output += '\tPort: %s\n' % data['port']
        output += '\tEnabled: %s\n' % data['enabled']
        return output


class VIP(CPDKModel):
    address = Column(String)
    virtual_id = Column(Integer, ForeignKey('virtualserver.id'))

    def __str__(self):
        return self.address


class VirtualServer(CPDKModel):
    port = Column(Integer)
    enabled = Column(Boolean,
                     info={'negative_cmd': 'disabled'})

    # Servers associated with this virtual server (many-to-many)
    servers = relationship('Server',
                           secondary=Server_VS_Map)

    # List of VIP's associated with this virtual server (many-to-one)
    vips = relationship('VIP')

    display_name = 'virtual'

    @staticmethod
    def show(data):
        output = 'Virtual Server: %s\n' % data['name']
        output += '\tPort: %s\n' % data['port']
        output += '\tEnabled: %s\n' % data['enabled']

        if len(data['vips']):
            output += '\tVirtual IPs:\n'
            for vip in data['vips']:
                output += '\t\t%s\n' % vip
            output += '\n'

        if len(data['servers']):
            output += '\tServers:\n'
            for server in data['servers']:
                output += '\t\t%s\n' % server

        return output
