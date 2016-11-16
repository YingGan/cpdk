#!/usr/bin/python
import cmd
import zmq
import settings
from cpdk_db import import_user_models


class BaseCmd(cmd.Cmd):
    intro = None
    file = None

    def do_exit(self, _):
        return True


def enter_mode(cls, arg):
    print cls
    cls.cmdloop()


class RedShell(BaseCmd, object):
    intro = 'Welcome to RedShell! Type help or ? to list commands\n'
    prompt = '>'

    @staticmethod
    def setup_methods(models):

        # Create shadow 'shell' classes for each config item
        shell_classes = []
        for model in models:
            cls = type(model.__class__ .__name__ + 'Shell', (BaseCmd, object,), {'model': model})
            cls.enter_mode = classmethod(enter_mode)

            # TODO: Build do_XYZ commands for each member
            shell_classes.append(cls)

        # Setup 'do' methods for each model
        for shell_class in shell_classes:
            method_name = 'do_' + shell_class.model.__class__.__name__
            setattr(RedShell, method_name, classmethod(enter_mode))


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
