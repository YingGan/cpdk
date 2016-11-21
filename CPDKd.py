#!/usr/bin/python
"""
Control Plane Development Kit (CPDK) Daemon
 This daemon is responsible for processing messages, interacting with the database, and providing a REST endpoint.
"""
import zmq
import signal
import logging
import settings
import argparse
from cpdk_db import import_user_models

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

# Global flag to indicate if the daemon should keep processing in its main loop
is_running = True
engine = create_engine('sqlite:///' + settings.DB_NAME, echo=settings.DEBUG)
Session = sessionmaker(bind=engine)
user_models = None


def signal_handler(sig, frame):
    """
    Generic signal handler for catching Ctrl+C
    :param sig:
    :param frame:
    :return: None
    """
    del sig, frame   # Nobody likes unused arguments
    global is_running
    is_running = False
    logging.info('^C')
signal.signal(signal.SIGINT, signal_handler)


def setup_zmq():
    """
    Create a Zero Message Queue server and start listening on the designated port
    :return: The zmq socket object
    """
    context = zmq.Context()
    zmq_socket = context.socket(zmq.REP)
    zmq_listen_addr = "tcp://*:" + str(settings.ZMQ_SHELL_PORT)

    logging.info('Starting ZMQ server on %s' % zmq_listen_addr)
    zmq_socket.bind(zmq_listen_addr)
    return zmq_socket


def process_msg(msg):
    """
    Process an incoming message.
    :param msg: The message, as received from the ZMQ socket
    Expected format is a Python dictionary with the following members:
        t - The type of message (get_or_create | get | create | modify | delete | list | add_ref | del_ref)
        o - The class of object being worked on
        on - The name of the object instance being worked on (optional for list commands only)
        (optional) f - Name of the field for the object
        (optional) fv - Value for the field
    :return: The response to be sent to the client
    """
    response = {'status': 'ok'}
    logging.debug("Received request: %s " % str(msg))
    model = user_models[msg['o']]
    session = Session()

    if msg['t'] == 'get_or_create':     # Get an object, create it if it doesn't exist
        try:
            q_result = session.query(model.__class__).filter(model.__class__.name == msg['on']).one()
            response['result'] = 'exists'
            response['id'] = q_result.id
        except NoResultFound:
            new_model = model.__class__()
            new_model.name = msg['on']
            session.add(new_model)
            session.commit()
            response['result'] = 'created'
            response['id'] = new_model.id

    elif msg['t'] == 'get':     # Get an object
        # TODO: Write this
        pass
    elif msg['t'] == 'create':  # Create a new object
        # TODO: Write this
        pass
    elif msg['t'] == 'delete':  # Delete a field or object
        try:
            q_result = session.query(model.__class__).filter(model.__class__.name == msg['on'])
            if q_result.count() is 0:
                response['status'] = 'error'
                response['message'] = '%s %s not found' % (model.__class__.__name__, msg['on'])
            q_result.delete()
            session.commit()
        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__.__name__, msg['on'])

    elif msg['t'] == 'list':    # List model's fields
        try:
            if 'on' in msg:
                q_result = session.query(model.__class__).filter(model.__class__.name == msg['on']).all()
                if len(q_result) is 0:
                    response['status'] = 'error'
                    response['message'] = '%s %s not found' % (model.__class__.__name__, msg['on'])
            else:
                q_result = session.query(model.__class__).all()

            response['result'] = q_result

        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__.__name__, model.__class__.name)
        print response

    elif msg['t'] == 'modify':  # Modify a field

        try:
            q_result = session.query(model.__class__).filter(model.__class__.name == msg['on']).one()
            setattr(q_result, msg['f'], msg['fv'])
            session.commit()

        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__, model.__class__.name)

    elif msg['t'] == 'add_ref':     # Add a reference to another object
        # TODO: Write this
        pass
    elif msg['t'] == 'del_ref':     # Delete an object reference
        # TODO: Write this
        pass
    else:
        response = {'status': 'error', 'message': 'unknown type %s' % msg['msg']}

    return response


def main():
    """
    Main entry point for the daemon
    :return: None
    """
    global is_running
    global user_models

    if settings.DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description='Control Plane Development Kit Daemon)')

    # Import the database schema
    user_models = import_user_models()

    # Setup the ZeroMQ socket
    zmq_socket = setup_zmq()

    # Start the message loop
    while is_running:
        try:
            msg = zmq_socket.recv_pyobj(flags=zmq.NOBLOCK)
            zmq_socket.send_pyobj(process_msg(msg))
        except zmq.ZMQError, e:
            if e.errno == zmq.EAGAIN:
                # TODO: Sleep a little bit here?
                continue
if __name__ == '__main__':
    main()
