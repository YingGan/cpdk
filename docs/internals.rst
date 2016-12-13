.. _cpdk-internals:

##############
CPDK Internals
##############
This section describes CPDK internal APIs and protocols.

.. _cpdk-CPDKd-message-format:

==================================
CPDKd Client-Server Message Format
==================================
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


============================
CPDKd PUB-SUB Message Format
============================

Daemons can subscribe to be notified by CPDKd when configuration events occur. The messages sent by CPDKd will use
JSON-encoded strings as the message format.

Message Envelope
----------------
Each message will contain an 'envelope' to discern which model the event is being generated for.
The message envelope is a string with no key value and is also always the first value in the JSON response.

   **Design Note**

      *ZeroMQ uses these envelopes to filter messages to specific subscribers. When a daemon connects, it specifies
      which model it cares to receive messages for.*


Message Fields
--------------
Each JSON message has the following fields defined. The actual field name in the message is marked in parenthesis.

type
^^^^
An integer, designating the type of message that is being sent. The message types are as follows:

+-------------------+---+-------------------------------------------------------------------------------------+
|      Type         | ID| Description                                                                         |
+===================+===+=====================================================================================+
|   Create Object   | 1 | A new object has been created                                                       |
+-------------------+---+-------------------------------------------------------------------------------------+
|   Delete Object   | 2 | An existing object has been deleted                                                 |
+-------------------+---+-------------------------------------------------------------------------------------+
|   Modify Field    | 3 | An existing object's field has been modified                                        |
+-------------------+---+-------------------------------------------------------------------------------------+
|   Add Reference   | 4 | A new object reference has been added to the target object of the message           |
+-------------------+---+-------------------------------------------------------------------------------------+
| Delete Reference  | 5 | An existing object reference has been removed from the target object of the message |
+-------------------+---+-------------------------------------------------------------------------------------+
| Delete All Objects| 6 | All of the objects for a given model have been deleted                              |
+-------------------+---+-------------------------------------------------------------------------------------+


obj
^^^^
A string holding the name of the object being operated on in the message.

field
^^^^^
Only used in modify, add reference, and delete reference messages.

For modify messages, this is the name of the field in the object which has been modified.
For add and delete reference messages this is the model type of the referring object.

value
^^^^^
Only used in modify, add reference, and delete reference messages.

For modify messages, this is the new value of the field.
For add and delete reference messages, this is the name of the object of the referring object.

Examples
--------

In these examples, assume the following models have been defined: ::

   class DepartmentModel(CPDKModel):
      employees = relationship("EmployeeModel")

   class EmployeeModel(CPDKModel):
      salary = Column(Float)
      department_id = Column(Integer, ForeignKey('departmentmodel.id'))

A new EmployeeModel has been created ::

   ['EmployeeModel', {'type': 1, 'obj': 'John Doe'}]

An existing EmployeeModel has been deleted ::

   ['EmployeeModel', {'type': 2, 'obj': 'John Doe'}]

Change the salary field for an EmployeeModel ::

   ['EmployeeModel', {'type': 3,
                      'obj': 'John Doe',
                      'field': 'salary',
                      'value': 75000.00}]

Add an EmployeeModel object reference to a DepartmentModel object ::

   ['DepartmentModel', {'type': 4,
                        'obj', 'Sales',
                        'field': 'EmployeeModel',
                        'value': 'John Doe'}]

Remove an EmployeeModel object reference from a DepartmentModel object ::

   ['DepartmentModel', {'type': 5,
                        'obj': 'Sales',
                        'field': 'EmployeeModel',
                        'value': 'John Doe'}]

Delete all EmployeeModel objects - *BE CAREFUL DOING THIS!* ::

   ['EmployeeModel', {'type': 6}]

