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

        display_name = 'employee'

Great! Our minion, er, employee, will have simple attributes such as first and last name, a salary, and a boolean to
note if they're a manager.


Model Relationships
-------------------
What fun is a database without relations? Don't answer that if you're a big-data fanboy, please. In this section, we'll
show how to add relations between database tables.

By defining relationships between models, CPDK will automatically generate the CLI commands to allow users to configure
those relationships. Additionally, CPDK will automatically generate the C++ methods to notify a daemon when the relationship
is established.

One To Many
^^^^^^^^^^^
The first type of relationship is the one-to-many type. In this scneario, one model can be linked multiple times to
another model.

Let's start by expanding our previous ``EmployeeModel`` example by adding a DepartmentModel. Since this is a
one-to-many relationship, we'll say that a department can have multiple employees (but not vice versa) ::

    from sqlalchemy.orm import relationship

    ...

    class DepartmentModel(CPDKModel):
        cost_code = Column(Integer)
        email_alias = Column(String)
        employees = relationship("EmployeeModel")

        display_name = 'department'

Now back in our ``EmployeeModel``, a ``ForeignKey`` is needed to instruct the ORM schema that we intend to link the two
models.

The new EmployeeModel class looks like this: ::

    class EmployeeModel(CPDKModel):
        first_name = Column(String)
        last_name = Column(String)
        salary = Column(Float)
        manager = Column(Boolean)
        department_id = Column(Integer, ForeignKey('departmentmodel.id')

The little bit of glue between these two models is performed by the department_id field. Note that it's just another
Integer-typed Column but this time it has a ForeignKey associated with it.

**STOP. Read this next line. Seriously.**

SQLAlchemy requires your foreign key name to be lowercase. Yes, it's just the model name, just lower-cased.

Great, now that the two models are linked, go ahead and update your database schema by running ``cpdk-util.py --syncdb``.
While you're at it, let's re-generate the CLI schema too: ``cpdk-util.py --buildcli``.

If you run CPDKd and RedShell you'll notice that the department mode now has an add/remove sub-command. These automatically
generated commands allow you to add and remove employees to a department record.

example: ::

    Global> employee Frank
    employee-Frank>exit
    Global> department sales
    department-sales> add EmployeeModel Frank
    department-sales> show department
    employees: ['Frank']
    department-sales>

**TODO:** *Use the display name when adding/removing a relationship. Right now, the model name must be used.*

Many To Many
^^^^^^^^^^^^
Another powerful relationship type is the many-to-many. In this situation, each side of the relationship can have
one or more links to the opposing side. Extending our Employee/Department scenario, let's say that Employees can now
be in mutliple departments. *Departments can still have multiple employees.*

SQLAlchemy achieves this by having a separate *association table*. ::

    emp_dep_map = Table('Employee_Department_Map', CPDKModel.metadata,
                        Column('employe_id', Integer, ForeignKey('employeemodel.id')),
                        Column('department_id', Integer, ForeignKey('departmentmodel.id')))

This model defines both sides of the relationship. As such, no ForeignKey is needed in the other models anymore. Our
employee and department models now look like this: ::

    class DepartmentModel(CPDKModel):
        cost_code = Column(Integer)
        email_alias = Column(String)
        employees = relationship("EmployeeModel", secondary=emp_dep_map)
        display_name = 'department'

    class EmployeeModel(CPDKModel):
        first_name = Column(String)
        last_name = Column(String)
        salary = Column(Float)
        manager = Column(Boolean)
        departments = relationship("DepartmentModel", secondary=emp_dep_map)

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

Custom 'show' command output
----------------------------
Every model has a CLI 'show' command generated for it by the '--buildcli' mode of ``cpdk-util.py``. By default,
every field in the model will simply be output as a key/value listing when the show command is run. By defining a
static ``show(data)`` function on the model, you can override that behavior.

The function will be passed a dictionary of data that can be used to access field values. The method needs to
return a string that will be printed to the output stream. ::

   class ServerModel(CPDKModel):
       port = Column(Integer)
       address = Column(String)

       @staticmethod
       def show(data):
           output = '=====%s=====\n' % data['name']
           output += 'port: %s\n' % data['port']
           output += 'address: %s\n' % data['address']
           return output

Remember, every model automatically has ``name`` and ``id`` parameters (defined in CPDKModel) which will be part of the
data dictionary.