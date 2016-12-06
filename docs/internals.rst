.. _cpdk-internals:

##############
CPDK Internals
##############
This section describes CPDK internal APIs and protocols.

.. _cpdk-CPDKd-message-format:

====================
CPDKd Message Format
====================
Client-Server communication with CPDKd uses a JSON-based messaging format over a ZeroMQ REQ-REP channel.
Every time a message is sent to CPDKd, a reply is issued in return. The response contains the status of the client
request and any data that may be required by the request.


Message Fields
--------------
Each JSON message has the following fields defined. The actual field name in the message is marked in parenthesis.

Type (t)
^^^^^^^^
(required) The message type can be one of the following values:

- get_or_create
- get
- create
- modify
- delete
- delete_all
- list
- add_ref
- del_ref

Object (o)
^^^^^^^^^^
(required) The object class to be operated on. This corresponds to the class named used when defining a model.

Object Name (on)
^^^^^^^^^^^^^^^^

(mostly required) The name of the object instance. Only optional for 'list' command types.

Field (f)
^^^^^^^^^
(optional) Name of the field to be operated on within the object.

Field Value (fv)
^^^^^^^^^^^^^^^^
(optional) Value for the field to be operated on.

Reference Value (rv)
^^^^^^^^^^^^^^^^^^^^
(add_ref and del_ref commands) The field name in the model which holds the relationship()

Message Response
----------------
Every time CPDKd receives a message, a response is generated (as is required by ZeroMQ REQ-REP socket type).

The JSON-formatted response will always contain the key 'status'. It's a string which is either 'ok' or some other
message. If status is not 'ok', the key 'message' will be present and contain a more detailed error description.
Some messages return additional keys and are outlined below.

get_or_create
^^^^^^^^^^^^^
- result: 'exists' or 'created'
- id: The ID of the newly created, or fetched, object

get
^^^^
- id: ID of the fetched object

create
^^^^^^
- id: ID of the created object

list
^^^^
- result: A list of one or more JSON objects, each containing the fields for the request.


Examples
--------

The following section shows examples of client requests and CPDKd responses. ::

   c: {'t': 'get_or_create', 'o': 'Server', 'on': 'MyCoolServer'}
   s: {'status': 'ok', 'result': 'created', 'id': 123}

   c: {'t': 'list', 'o': 'Server'}
   s: {'status': 'ok', 'result': [{'id': 123, 'name': 'MyCoolServer', 'address': None}]

   c: {'t': 'delete', 'o': 'Server', 'on': 'InvalidServerName'}
   s: {'status': 'error', 'message': 'Server InvalidServerName not found'}

   c: {'t': 'add_ref', 'o': 'Server', 'on': 'MyCoolServer', 'f': 'Address', 'fv': 'management', 'rv': 'addresses'}
   s: {'status': 'ok'}
