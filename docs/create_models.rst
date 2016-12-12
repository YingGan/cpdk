Defining Models
===============

In order to define what data is stored in your database, made available on the CLI,
or shared with listening daemons, it needs to be modeled. The process of modeling data is done by
defining it as Python classes.

Let's start with a simple example of defining how we'd like to represent an employee in ye olde database: ::

    from cpdk_db import CPDKModel
    from sqlalchemy import String, Float, Boolean

    class EmployeeModel(CPDKModel):
        first_name = Column(String)
        last_name = Column(String)
        salary = Column(Float)
        manager = Column(Boolean)

Great! Our minion, er, employee, will have simple attributes such as first and last name, a salary, and a boolean to
note if they're a manager.

Special Members
---------------
To customize how CPDK interacts with a model, you can declare specific fields, which will not be added to the database.

daemon_managed
^^^^^^^^^^^^^^
``daemon_managed = True``

Declaring this field, and setting it to True, declares it as being managed by your application daemons. Effectively,
application daemons are the only way these objects can be created. An example of an object that may fit this use case
would be an ethernet port. The user can't declare one on the CLI, they're always present, but they may be able to
interact with it, such as enabling or disabling it.

display_name
^^^^^^^^^^^^
``display_name = 'employee'``

If you don't want CPDK to use the model name as the CLI mode, it can be overriden with this field. Specify any string
that you want to change the display name to.

example ::

    class ServerModel(CPDKModel):
        port = Column(Integer)
        display_name = 'server'

Now on the CLI ::

    Global> server univac
    server-univac>

Boolean Inverse
---------------

By default, CPDK will generate a cli command to disable your boolean field. The command is ``no_yourflag``.
In order to avoid the 'no something' syntax, CPDK allows you to specify a command name within the field.
The command is specified as the ``negative_cmd`` option within the ``info`` dictionary.

In the example below, the enabled command will be negated with a new command, 'disabled' ::

    enabled = Column(Boolean, default=False,
                     info={'negative_cmd': 'disabled'})
