#!/usr/bin/python
"""
Control Plane Development Kit (CPDK) Daemon
 This daemon is responsible for processing messages, interacting with the database, and providing a REST endpoint.
"""
import sys
import zmq
import settings
import argparse
from cpdk_db import import_user_models

# The 0MQ socket to listen on
zmq_socket = None


def setup_zmq():
    global zmq_socket
    context = zmq.Context()
    zmq_socket = context.socket(zmq.REQ)
    zmq_socket.connect("tcp://localhost:" + str(settings.ZMQ_PORT))


def main():
    """
    Main entry point for the daemon
    :return: None
    """
    parser = argparse.ArgumentParser(description='Control Plane Development Kit Daemon)')
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Import the database schema
    models = import_user_models()

    # Start listening on the ZeroMQ socket
    setup_zmq()

if __name__ == '__main__':
    main()
