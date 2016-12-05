#!/usr/bin/python
"""
Control Plane Development Kit (CPDK) Daemon
 This daemon is responsible for processing messages, interacting with the database, and providing a REST endpoint.
"""
import zmq
import sys
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
Session = None
user_models = None

# Command IDs for the PUB-SUB channel
CMD_ID_CREATE = 1
CMD_ID_DELETE = 2
CMD_ID_MODIFY = 3
CMD_ID_ADDREF = 4
CMD_ID_DELREF = 5
CMD_ID_DELETE_ALL = 6


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


def setup_pubsub_zmq():
    """
    Create a Zero Message Queue publisher
    :return: The zmq socket object
    """
    context = zmq.Context()
    zmq_socket = context.socket(zmq.PUB)
    zmq_listen_addr = "tcp://*:" + str(settings.ZMQ_PUBSUB_PORT)
    logging.info('Starting ZMQ PubSub server on %s' % zmq_listen_addr)
    zmq_socket.bind(zmq_listen_addr)
    return zmq_socket


def setup_daemon_zmq():
    """
    Create a Zero Message Queue socket that daemons can interact with
    :return: The zmq socket object
    """
    context = zmq.Context()
    zmq_socket = context.socket(zmq.REP)
    zmq_listen_addr = "tcp://*:" + str(settings.ZMQ_CLIENT_SERVER_PORT)
    logging.info('Starting ZMQ conf pull server on %s' % zmq_listen_addr)
    zmq_socket.bind(zmq_listen_addr)
    return zmq_socket


def setup_cli_zmq():
    """
    Create a Zero Message Queue server and start listening on the designated port
    :return: The zmq socket object
    """
    context = zmq.Context()
    zmq_socket = context.socket(zmq.REP)
    zmq_listen_addr = "tcp://*:" + str(settings.ZMQ_SHELL_PORT)

    logging.info('Starting ZMQ CLI server on %s' % zmq_listen_addr)
    zmq_socket.bind(zmq_listen_addr)
    return zmq_socket


def process_client_msg(msg):
    """
    Process a unicast client request message
    :param msg: Message dictionary.
        Currently only contains one member: 'object'. This is the table name to query.
    :return: A python dictionary containing dictionaries of each object found
    """
    response = {}

    model = user_models[msg['object']]
    session = Session()
    q_result = session.query(model.__class__).all()

    for r in q_result:
        entry = {}
        for column in r.__table__.columns:

            # Skip over these special fields
            if column.name == 'name' or column.name == 'id':
                continue

            entry[column.name] = getattr(r, column.name)

        response[r.name] = entry

    return response


def process_config_msg(msg, zmq_pub_socket):
    """
    Process a configuration message.
    :param msg: The message, as received from the ZMQ socket
    Expected format is a JSON object with the following members:
        t - The type of message (get_or_create | get | create | modify | delete | delete_all | list | add_ref | del_ref)
        o - The class of object being worked on
        on - The name of the object instance being worked on (optional for list commands only)
        (optional) f - Name of the field for the object
        (optional) fv - Value for the field
    :param zmq_pub_socket: The ZMQ socket to be used for PUBLISH messages
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

            # Send out the PUB-SUB message
            zmq_pub_socket.send_json([model.__class__.__name__, {'type': CMD_ID_CREATE, 'obj': msg['on']}])

    elif msg['t'] == 'get':     # Query for the existence of an object
        try:
            q_result = session.query(model.__class__).filter(model.__class__.name == msg['on']).one()
            response['id'] = q_result.id
        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__.__name__, msg['on'])

        print response

    elif msg['t'] == 'create':  # Create a new object
        new_model = model.__class__()
        new_model.name = msg['on']
        session.add(new_model)
        session.commit()
        response['result'] = 'created'
        response['id'] = new_model.id

        # Send out the PUB-SUB message
        zmq_pub_socket.send_json([model.__class__.__name__, {'type': CMD_ID_CREATE, 'obj': msg['on']}])
        pass
    elif msg['t'] == 'delete':  # Delete a field or object
        try:
            q_result = session.query(model.__class__).filter(model.__class__.name == msg['on'])
            if q_result.count() is 0:
                response['status'] = 'error'
                response['message'] = '%s %s not found' % (model.__class__.__name__, msg['on'])
            else:
                q_result.delete()
                session.commit()
                # Send out the PUB-SUB message
                zmq_pub_socket.send_json([model.__class__.__name__, {'type': CMD_ID_DELETE, 'obj': msg['on']}])

        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__.__name__, msg['on'])

    elif msg['t'] == 'delete_all':
        q_result = session.query(model.__class__)
        q_result.delete()
        session.commit()

        # Send out a notification to all deamons to delete their local copies
        zmq_pub_socket.send_json([model.__class__.__name__, {'type': CMD_ID_DELETE_ALL}])

    elif msg['t'] == 'list':    # List model's fields
        try:
            if 'on' in msg:
                q_result = session.query(model.__class__).filter(model.__class__.name == msg['on']).all()
                if len(q_result) is 0:
                    response['status'] = 'error'
                    response['message'] = '%s %s not found' % (model.__class__.__name__, msg['on'])
            else:
                q_result = session.query(model.__class__).all()

            response['result'] = []

            for obj in q_result:
                response['result'].append(obj.serialize())

        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__.__name__, model.__class__.name)

    elif msg['t'] == 'modify':  # Modify a field

        try:
            q_result = session.query(model.__class__).filter(model.__class__.name == msg['on']).one()
            setattr(q_result, msg['f'], msg['fv'])
            session.commit()

            # Send out the PUB-SUB message
            zmq_pub_socket.send_json([model.__class__.__name__, {'type': CMD_ID_MODIFY,
                                                                 'obj': msg['on'],
                                                                 'field': msg['f'],
                                                                 'value': getattr(q_result, msg['f'])}])

        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__, model.__class__.name)

    elif msg['t'] == 'add_ref':     # Add a reference to another object
        try:
            # First, lookup the object we're going to add the reference TO
            q_result = session.query(model.__class__).filter(model.__class__.name == msg['on']).one()

            # Next, lookup the object to be ADDED to the base
            ref_model = user_models[msg['f']]
            try:
                q_ref_obj = session.query(ref_model.__class__).filter(ref_model.__class__.name == msg['fv']).one()

                getattr(q_result, msg['rv']).append(q_ref_obj)
                session.commit()

                # Send out PUBSUB message that the relationship was added
                zmq_pub_socket.send_json([model.__class__.__name__, {'type': CMD_ID_ADDREF,
                                                                     'obj': msg['on'],
                                                                     'field': msg['f'],
                                                                     'value': msg['fv']}])
            except NoResultFound:
                response['status'] = 'error'
                response['message'] = '%s %s not found' % (ref_model.__class__.__name__, msg['fv'])

        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__, model.__class__.name)
    elif msg['t'] == 'del_ref':     # Delete an object reference
        try:
            # First, lookup the object we're going to add the reference TO
            q_result = session.query(model.__class__).filter(model.__class__.name == msg['on']).one()

            # Next, lookup the object to be ADDED to the base
            ref_model = user_models[msg['f']]
            try:
                q_ref_obj = session.query(ref_model.__class__).filter(ref_model.__class__.name == msg['fv']).one()
                try:
                    getattr(q_result, msg['rv']).remove(q_ref_obj)
                    session.commit()

                    # Send out PUBSUB message that the relationship was added
                    zmq_pub_socket.send_json([model.__class__.__name__, {'type': CMD_ID_DELREF,
                                                                         'obj': msg['on'],
                                                                         'field': msg['f'],
                                                                         'value': msg['fv']}])
                except ValueError:
                    response['status'] = 'error'
                    response['message'] = '%s is not associated with this object' % msg['fv']
            except NoResultFound:
                response['status'] = 'error'
                response['message'] = '%s %s not found' % (ref_model.__class__.__name__, msg['fv'])

        except NoResultFound:
            response['status'] = 'error'
            response['message'] = '%s %s not found' % (model.__class__, model.__class__.name)
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
    parser.add_argument('--settings', help='python path to settings file', dest='settings')

    args = vars(parser.parse_args())

    if args['settings']:
        global settings
        settings = __import__(args['settings'], globals(), locals(), ['DB_NAME', 'DEBUG'], -1)
    else:
        import settings

    global Session
    engine = create_engine('sqlite:///' + settings.DB_NAME, echo=settings.DEBUG)
    Session = sessionmaker(bind=engine)

    # Import the database schema
    user_models = import_user_models(settings.MODELS_DIR)

    # Setup the ZeroMQ socket for the CLI daemon
    zmq_cli_socket = setup_cli_zmq()

    # Setup the socket to be used for PUB-SUB channels
    zmq_pub_socket = setup_pubsub_zmq()

    # Setup the socket to be used for
    zmq_daemon_socket = setup_daemon_zmq()

    # Start the message loop
    while is_running:
        try:
            # Process CLI events
            msg = zmq_cli_socket.recv_json(flags=zmq.NOBLOCK)
            logging.info('CLI request: %s' % msg)
            zmq_cli_socket.send_json(process_config_msg(msg, zmq_pub_socket))
        except zmq.ZMQError, e:
            if e.errno == zmq.EAGAIN:
                pass

        try:
            # Process any direct client requests
            msg = zmq_daemon_socket.recv_json(flags=zmq.NOBLOCK)
            # zmq_daemon_socket.send_json(process_client_msg(msg))
            zmq_daemon_socket.send_json(process_config_msg(msg, zmq_pub_socket))

        except zmq.ZMQError, e:
            if e.errno == zmq.EAGAIN:
                pass

        # TODO: Sleep a little bit here to save the poor CPU?

if __name__ == '__main__':
    main()
