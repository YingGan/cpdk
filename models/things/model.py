from cpdk_db import CPDKModel
from sqlalchemy import Integer, Column, String, Boolean, BigInteger


class Interface(CPDKModel):
    enabled = Column(Boolean, default=False,
                     info={'negative_cmd': 'disabled'})

    packets_out = Column(BigInteger, default=0,
                         info={'display_only': True})  # No CLI command will be generated
    packets_in = Column(BigInteger, default=0,
                        info={'display_only': True})    # No CLI command will be generated

    daemon_managed = True  # This model can only be created/deleted by daemons


class Server(CPDKModel):
    something = Column(Integer)

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

    def __str__(self):
        output =  'Virtual Server: %s\n' % self.name
        output += '\tAddress: %s\n' % self.address
        output += '\tPort: %s\n' % self.port
        output += '\tEnabled: %s\n' % self.enabled
        return output
