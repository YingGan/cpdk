#!/usr/bin/python
import os
import cmd
import zmq
import inspect
import settings
from cpdk_db import CPDKModel
from cpdk_db import import_user_models


class BaseCmd(cmd.Cmd):
    intro = None
    file = None

    def do_exit(self, _):
        return True


MODE_TEMPLATE = '''
    class %s(cmd.Cmd):
        intro = None
        prompt = %s

        def do_exit(self, arg):
            return True
'''


class CLIParseMode(object):
    name = ""
    child_modes = []
    child_commands = []

    def __init__(self, name):
        self.name = name

    def add_child_mode(self, mode):
        self.child_modes.append(mode)

    def add_child_command(self, command):
        self.child_commands.append(command)


class CLIParseCmd(object):
    name = ""
    fields = []

    def __init__(self, name):
        self.name = name


class CLIParseField(object):
    name = ""

    def __init__(self, name):
        self.name = name


def build_cli_recurse(parent_dir, parent_mode):

    # Look for files and directories inside of parent_dir
    for obj in os.listdir(parent_dir):
        full_path = parent_dir + os.path.sep + obj

        if os.path.isfile(full_path):
            # print "File: %s" % full_path

            # Skip over special files or non-python files
            if obj.startswith('__') or (obj.endswith('.py') is False):
                continue

            # Change from a file system path to a dotted module path (remove .py)
            import_path = full_path.replace('.py', '')
            from_path = parent_dir.replace(os.path.sep, '.')
            module_path = import_path.replace(os.path.sep, '.')

            # Import the module
            print "importing %s" % module_path
            import_namespcae = __import__(module_path, fromlist=[from_path])

            for name, o in inspect.getmembers(import_namespcae, inspect.isclass):
                if inspect.isclass(o):
                    print "name: %s" % name
                    print "obj: %s" % o
            # all_my_base_classes = {cls.__name__: cls for cls in CPDKModel.__subclasses__()}


        elif os.path.isdir(full_path):
            # print "Dir: %s" % full_path
            new_mode = CLIParseMode(name=obj)
            parent_mode.add_child_mode(new_mode)
            build_cli_recurse(full_path, new_mode)
        else:
            pass


def build_cli():
    """
    Walk through the settings.MODELS_DIR and build the CLI schema.
     Directories are treated as empty mode containers.

    :return: None
    """
    global_mode = CLIParseMode(name='global')

    # fh = open(settings.SHELL_SCHEMA_FILE)

    # build_cli_recurse(os.path.abspath(settings.MODELS_DIR))
    build_cli_recurse(settings.MODELS_DIR, global_mode)





class RedShell(BaseCmd, object):
    intro = 'Welcome to RedShell! Type help or ? to list commands\n'
    prompt = '>'

    @staticmethod
    def setup_methods(models):

        # Create shadow 'shell' classes for each config item
        shell_classes = []
        for model in models:

            '''
            decl = 'class %sShell(cmd.Cmd):\n' % model.__class__ .__name__
            decl += '   prompt="%s>"\n' % model.__class__ .__name__
            decl += '   intro=""\n'
            exec decl in globals(), locals()
            print decl
            '''
            shell_class_name = model.__class__.__name__ + 'Shell'
            cls = type(model.__class__ .__name__ + 'Shell', (cmd.Cmd, object), {'prompt': '%s>' % model.__class__ .__name__})
            print cls
            # cls.enter_mode = classmethod(enter_mode)
            # shell_class = locals()[model.__class__ .__name__ + 'Shell']
            # print shell_class

            # TODO: Build do_XYZ commands for each member
            #shell_classes.append(cls)

            dyn_method_name = 'redshell_enter_' + shell_class_name
            dynamic_method = 'def %s(self, arg):\n' % dyn_method_name
            dynamic_method += '    print locals()["%s"]\n' % shell_class_name
            #dynamic_method += '    from __main__ import %s\n' % shell_class.__name__
            # dynamic_method += '    import %s\n' % shell_class.__name__
            dynamic_method += '    %s().cmdloop()\n' % shell_class_name
            print dynamic_method
            exec dynamic_method

            method_name = 'do_' + model.__class__.__name__
            setattr(RedShell, method_name, locals()[dyn_method_name])

    def cmdloop(self, intro=None):
        print self.intro
        while True:
            try:
                super(RedShell, self).cmdloop(intro='')
                self.postloop()
                break
            except KeyboardInterrupt as e:
                print('^C')

if __name__ == '__main__':
    context = zmq.Context()
    zmq_socket = context.socket(zmq.REQ)
    zmq_socket.connect("tcp://localhost:" + str(settings.ZMQ_PORT))

    models = import_user_models()

    RedShell.setup_methods(models)
    shell = RedShell()

    shell.cmdloop()
