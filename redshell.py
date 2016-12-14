#!/usr/bin/python
import os
import zmq                      # Zero Message Queue
import argparse
import inspect                  # Because, let's be honest, meta programming is cool
from cpdk_db import CPDKModel, import_user_models
import sqlalchemy
from sqlalchemy.inspection import inspect as sql_inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute

# This has to be global as it will be accessed by classes in the schema
zmq_socket = None


class CLIParseMode(object):
    """
    Special class which represents a 'mode' for the CLI. Modes are simply directories in the models hierarchy.
    Each mode must have handlers in place for all the commands found within that mode.
    """
    name = ""
    child_modes = []
    child_commands = []

    def __init__(self, name):
        self.name = name
        self.child_modes = []
        self.child_commands = []

    def add_child_mode(self, mode):
        self.child_modes.append(mode)

    def add_child_command(self, command):
        self.child_commands.append(command)

    def get_commands(self, child_commands=None):
        """
        Recursively build a list of all CLIParseCmd's within this mode
        :return: A list of CLIParseCmd objects
        """
        if child_commands:
            child_commands.extend(self.child_commands)
        else:
            child_commands = self.child_commands

        for mode in self.child_modes:
            child_commands.extend(mode.get_commands(child_commands))

        return child_commands

    def build_cli(self, fh):
        """
        Write handlers to the schema file.
        :param fh: File handle
        :return: None
        """

        output = '\n'
        output += 'class %s(BaseCmd):\n' % self.name
        output += '    prompt = "%s>"\n' % self.name
        if self.name == 'Global':
            output += '    zmq_socket = None\n'
            output += '    models = None\n'

        # Add mode accessors for any commands in this mode
        for command in self.child_commands:
            output += '\n'
            output += '    def do_%s(self, arg):\n' % command.model.get_display_name()
            output += '        mode = %s()\n' % command.name

            # If the model is managed by daemons, disallow creation of one via the CLI
            if hasattr(command.model, 'daemon_managed') and command.model.daemon_managed:
                output += '        Global.zmq_socket.send_json({"t": "get", "o": "%s", "on": arg})\n' % command.name
            else:
                output += '        Global.zmq_socket.send_json({"t": "get_or_create", "o": "%s", "on": arg})\n' % command.name
            output += '        s = Global.zmq_socket.recv_json()\n'
            output += '        if s["status"] != "ok":\n'
            output += '            print s["message"]\n'
            output += '            return\n'
            output += '        mode.name = arg\n'
            output += '        mode.prompt = "%s-" + arg + ">"\n' % command.model.get_display_name()
            output += '        mode.cmdloop()\n'

        # Add handlers for any nested modes within this mode
        for mode in self.child_modes:
            output += '\n'
            output += '    def do_%s(self, arg):\n' % mode.name
            output += '        %s().cmdloop()\n' % mode.name

        fh.write(output)

        # Write out the actual child command classes
        for command in self.child_commands:
            command.build_cli(fh)

        # Write out the actual child mode classes
        for child in self.child_modes:
            child.build_cli(fh)

    def __str__(self):
        return "Mode: %s" % self.name


class CLIParseCmd(object):
    """
    Represent a command (aka a model which inherits from CPDKModel)
    """
    name = ""
    fields = []

    def __init__(self, name, model):
        """
        Constructor.
        :param name: The name of the model
        :param model: The SQLAlchemy class (CPDKModel) this command maps to
        """
        self.name = name
        self.fields = []
        self.model = model

    def __str__(self):
        return self.name

    def add_field(self, field):
        self.fields.append(field)

    def build_cli(self, fh):
        """
        Write the class to the schema file, which is used by cmd.Cmd in RedShell
        :param fh: File handle object
        :return: None
        """
        output = '\n\n'
        output += 'class %s(BaseCmd):\n' % self.name
        output += '    prompt = "%s>"\n' % self.model.get_display_name()

        # For each RelationshipProperty that doesn't have no_cli=True, create add commands
        i = sql_inspect(self.model)

        # Search through all of the relationships, checking for the 'read-only' info hash key
        # If all relationships are read-only, don't generate add or delete commands
        has_relationships = False
        for rel in i.mapper.relationships:
            if 'read-only' not in rel.info or rel.info['read-only'] is False:
                has_relationships = True

        if len(i.mapper.relationships) and has_relationships:

            output += '\n'
            output += '    def do_add(self, args):\n'
            output += '        arg_list = args.split(" ")\n'
            output += '        if len(arg_list) < 2:\n'
            output += '            print "*** ERROR: not enough arguments"\n'
            output += '            return\n'

            # The keys of the relationships are simply the field names in the model
            # ex: this->> *virtual_servers* = relalationship('VirtualServer'....)
            # Shipping this over to the server (ref_field) so it knows the field name to add the reference to
            for rel in i.mapper.relationships.keys():

                # Skip adding this relationship
                if 'read-only' in i.mapper.relationships[rel].info and i.mapper.relationships[rel].info['read-only']:
                    continue

                output += '        if arg_list[0] == "%s":\n' % i.mapper.relationships[rel].mapper.class_.__name__
                output += '            Global.zmq_socket.send_json({"t": "add_ref", "o": "%s", "on": self.name, "f": arg_list[0], "fv": arg_list[1], "rv": "%s"})\n' % (self.name, rel)
                output += '            s = Global.zmq_socket.recv_json()\n'
                output += '            if s["status"] != "ok":\n';
                output += '                print s["message"]\n'
                output += '\n'

        # For each RelationshipProperty, create remove commands
        if len(i.mapper.relationships) and has_relationships:
            output += '\n'
            output += '    def do_remove(self, args):\n'
            output += '        arg_list = args.split(" ")\n'
            output += '        if len(arg_list) < 2:\n'
            output += '            print "*** ERROR: not enough arguments"\n'
            output += '            return\n'

            for rel in i.mapper.relationships.keys():

                # Skip adding this relationship
                if 'read-only' in i.mapper.relationships[rel].info and i.mapper.relationships[rel].info['read-only']:
                    continue

                output += '        if arg_list[0] == "%s":\n' % i.mapper.relationships[rel].mapper.class_.__name__
                output += '            Global.zmq_socket.send_json({"t": "del_ref", "o": "%s", "on": self.name, "f": arg_list[0], "fv": arg_list[1], "rv": "%s"})\n' % (self.name, rel)
                output += '            s = Global.zmq_socket.recv_json()\n'
                output += '            if s["status"] != "ok":\n';
                output += '                print s["message"]\n'
                output += '\n'

        fh.write(output)

        # Write out all the handlers for fields in the model
        for field in self.fields:
            field.build_cli(fh)


class CLIParseField(object):
    """
    Represent an individual field within a model class
    """
    name = ""

    def __init__(self, name, parent_cmd, column, obj_type):
        """
        Constructor
        :param name: Name of the parameter
        :param parent_cmd: The CLIParseCmd object under which this field lives
        :param column: The SQLAlchemy Column object representing this field
        :param obj_type:
        """
        self.name = name
        self.parent_cmd = parent_cmd
        self.column = column
        self.obj_type = obj_type

    def build_cli(self, fh):
        """
        Write the accessor CLI commands for this field to the schema file
        :param fh: File Handle
        :return: None
        """

        # Skip creating a command if the field is display-only
        if 'display_only' in self.column.info and self.column.info['display_only']:
            return

        output = '\n'

        # Special case for booleans
        if self.obj_type == sqlalchemy.types.Boolean:
            # The affirmative version of the command
            output += '    def do_%s(self, arg):\n' % self.name
            output += '        Global.zmq_socket.send_json({"t": "modify", "o": "%s", "on": self.name, "f": "%s", "fv": True})\n' % (self.parent_cmd.name, self.name)
            output += '        s = Global.zmq_socket.recv_json()\n'
            output += '        if s["status"] != "ok":\n'
            output += '            print s["status"]\n'
            output += '\n'

            # The negative version of the command
            if 'negative_cmd' in self.column.info:
                output += '    def do_%s(self, arg):\n' % self.column.info['negative_cmd']
            else:
                output += '    def do_no_%s(self, arg):\n' % self.name
            output += '        Global.zmq_socket.send_json({"t": "modify", "o": "%s", "on": self.name, "f": "%s", "fv": False})\n' % (self.parent_cmd.name, self.name)
            output += '        s = Global.zmq_socket.recv_json()\n'
            output += '        if s["status"] != "ok":\n'
            output += '            print s["status"]\n'
        else:

            output += '    def do_%s(self, arg):\n' % self.name

            # Verify the paramter is of the correct type
            output += '        try:\n'
            if self.obj_type == sqlalchemy.types.Integer:
                output += '            arg = int(arg)\n'
            elif self.obj_type == sqlalchemy.types.BigInteger:
                output += '            arg = long(arg)\n'
            elif self.obj_type == sqlalchemy.types.String or self.obj_type == sqlalchemy.types.Text:
                output += '            arg = str(arg)\n'
            elif self.obj_type == sqlalchemy.types.Float:
                output += '            arg = float(arg)\n'
            else:
                raise NotImplemented
            output += '        except ValueError as e:\n'
            output += '            print e\n'
            output += '            return\n'
            output += '        Global.zmq_socket.send_json({"t": "modify", "o": "%s", "on": self.name, "f": "%s", "fv": arg})\n' % (self.parent_cmd.name, self.name)
            output += '        s = Global.zmq_socket.recv_json()\n'
            output += '        if s["status"] != "ok":\n';
            output += '            print s["status"]\n'
        fh.write(output)


def build_cli_recurse(parent_dir, parent_mode):
    """
    Walk through a directory and build command/mode/field nodes as appropriate
    :param parent_dir: Full path of the parent directory
    :param parent_mode: The CLIParseMode object to serve as a parent to all nodes found
    :return: None
    """
    # Look for files and directories inside of parent_dir
    for obj in os.listdir(parent_dir):
        full_path = parent_dir + os.path.sep + obj

        if os.path.isfile(full_path):

            # Skip over special files or non-python files
            if obj.startswith('__') or (obj.endswith('.py') is False):
                continue

            # Change from a file system path to a dotted module path (remove .py)
            import_path = full_path.replace('.py', '')
            from_path = parent_dir.replace(os.path.sep, '.')
            module_path = import_path.replace(os.path.sep, '.')

            import_namespcae = __import__(module_path, fromlist=[from_path])

            for name, o in inspect.getmembers(import_namespcae, inspect.isclass):
                # The 'name' != 'CPDKModel' check is to weed out the sqlalchemy Base class override
                if inspect.isclass(o) and issubclass(o, CPDKModel) and name != 'CPDKModel':
                    new_cmd = CLIParseCmd(name, o)
                    parent_mode.add_child_command(new_cmd)

                    for a in sql_inspect(o).mapper.column_attrs:

                        # Don't create commands for 'id' or 'name' fields
                        if a.key in ['id', 'name']:
                            continue

                        # If this column has foreign keys, skip it
                        if a.columns[0].foreign_keys:
                            continue
                        else:
                            field = CLIParseField(name=a.key, parent_cmd=new_cmd,
                                                  column=a.columns[0], obj_type=type(a.columns[0].type))
                            new_cmd.add_field(field)

        elif os.path.isdir(full_path):
            # Create a new mode object, add it to the parents object list, and recurse into it
            new_mode = CLIParseMode(name=obj)
            parent_mode.add_child_mode(new_mode)
            build_cli_recurse(full_path, new_mode)
        else:
            raise NotImplemented('Unknown file system object encountered during file scan')


def build_base(global_mode):
    """
    Define the base class, inherited by all command classes
    :param global_mode: The top level CLIParseMode
    :return: A string, containing the definition of the base class
    """
    base_def = '''
class BaseCmd(cmd.Cmd):
    intro = None
    file = None
    name = None

    def do_exit(self, _):
        return True

    def default_show(self, data):
        output = ''
        for key in data.keys():

            # Don't print object name or IDs
            if key == 'name' or key == 'id':
                continue

            output += "%s: %s\\n" % (key, data[key])
        return output

'''

    # Walk through the command tree and create global 'show' commands for each CLI command
    child_commands = global_mode.get_commands()

    base_def += '    def do_show(self, args):\n'

    # Put the outer 'if' statement here so that everything else can be an elif
    # TODO: Should this yield a warning?
    base_def += '        arg_list = args.split(" ")\n'
    base_def += '        if arg_list[0] == "":\n'
    base_def += '            print ""\n'

    for command in child_commands:
        base_def += '        elif arg_list[0] == "%s":\n' % command.model.get_display_name()
        base_def += '            zmq_cmd = None\n'
        base_def += '            if len(arg_list) == 1:\n'  # Show all elements
        base_def += '                zmq_cmd = {"t": "list", "o": "%s"}\n' % command.name
        base_def += '            elif len(arg_list) == 2:\n'
        base_def += '                zmq_cmd = {"t": "list", "o": "%s", "on": arg_list[1]}\n' % command.name
        base_def += '            Global.zmq_socket.send_json(zmq_cmd)\n'
        base_def += '            reply = Global.zmq_socket.recv_json()\n'
        base_def += '            if reply["status"] != "ok":\n'
        base_def += '                print reply["message"]\n'
        base_def += '                return\n'
        base_def += '            for r in reply["result"]:\n'
        base_def += '                m = getattr(Global.models["%s"], "show", None)\n' % command.name
        base_def += '                print m(r) if m else self.default_show(r)\n'
        base_def += '\n'

    # Walk through the command tree and create global 'delete' commands for each CLI command
    base_def += '    def do_delete(self, args):\n'
    base_def += '        arg_list = args.split(" ")\n'
    base_def += '        if len(arg_list) < 2:\n'
    base_def += '            print "Not enough argments (delete <mode> <item>)"\n'
    base_def += '            return\n'
    base_def += '        if arg_list[0] == "":\n'
    base_def += '            print "***ERROR: argument required"\n'
    base_def += '\n'
    for command in child_commands:

        base_def += '        elif arg_list[0] == "%s":\n' % command.model.get_display_name()

        # Daemon managed models can't be deleted via the CLI
        if hasattr(command.model, 'daemon_managed') and command.model.daemon_managed:
            base_def += '            print "%s objects can not be deleted"\n' % command.model.get_display_name()
        else:
            base_def += '            Global.zmq_socket.send_json({"t": "delete", "o": "%s", "on": arg_list[1]})\n' % command.name
            base_def += '            reply = Global.zmq_socket.recv_json()\n'
            base_def += '            if reply["status"] != "ok":\n'
            base_def += '                print reply["message"]\n'
            base_def += '                return\n'
            base_def += '\n'

    return base_def


def build_cli(base_dir, schema_file):
    """
    Walk through the base_dir and build the CLI schema.
     Directories are treated as empty mode containers.
    :param base_dir: The base directory to start recursion from
    :param schema_file: The name of the file to write to
    :return: None
    """

    global_mode = CLIParseMode(name='Global')

    # Generate a tree of all the modes, commands, and fields
    build_cli_recurse(base_dir, global_mode)

    # Write out the schema that cmd.Cmd can use when RedShell is invoked as a daemon
    fh = open(schema_file, mode='w')
    fh.write('import cmd\n')    # TODO: Upgrade to cmd2 to get more features?
    fh.write('\n')

    # Write out the base class that every command/mode will inherit
    fh.write(build_base(global_mode))

    global_mode.build_cli(fh)


def start_shell():
    """
    Kick off the shell by entering the CLI mode in the Global class
    :param schema_file: Name of the schema file to use
    :return: None
    """
    parser = argparse.ArgumentParser(description='RedShell')
    parser.add_argument('--settings', help='python path to settings file', dest='settings')

    args = vars(parser.parse_args())

    if args['settings']:
        global settings
        settings = __import__(args['settings'], globals(), locals(), ['DB_NAME', 'DEBUG'], -1)
    else:
        import settings

    global zmq_socket
    context = zmq.Context()
    zmq_socket = context.socket(zmq.REQ)
    zmq_socket.connect("tcp://localhost:" + str(settings.ZMQ_SHELL_PORT))

    # Import the schema and place all the objects in the global namespace
    module = __import__(settings.SHELL_SCHEMA_FILE.replace('.py', '').replace(os.path.sep, '.'), globals(), locals(), ['*'])
    for k in dir(module):
        globals()[k] = getattr(module, k)

    Global.zmq_socket = zmq_socket
    Global.models = import_user_models(settings.MODELS_DIR)
    Global().cmdloop(intro=settings.SHELL_LOGIN_BANNER)


if __name__ == '__main__':
    start_shell()
