// 3rd party requirements
#include <zmq.h>
#include <msgpack.hpp>

// Standard libraries
#include <stdio.h>
#include <string.h>
#include <cassert>

#define MSG_TYPE_CREATE 1
#define MSG_TYPE_DELETE 2
#define MSG_TYPE_MODIFY 3
#define MSG_TYPE_ADD_REF 4
#define MSG_TYPE_DELETE_REF 5

class {{ TEMPLATE }}Mgr {
public:
    void Init(void);
    void Cleanup(void);
    void ProcessMessageQueue(void);

    static {{ TEMPLATE }} & GetInstance() {
        static {{ TEMPLATE }} s_Instance;
        return s_Instance;
    }

private:
    void * m_ZMQSocket;
    void * m_ZMQContext;

    // Constructors (hidden for singleton-only access)
    {{ TEMPLATE }}();
    {{ TEMPLATE }}({{ TEMPLATE }}) const &);
    void operator=({{ TEMPLATE }} const&);
};

void {{ TEMPLATE }}::Init(void) {
    m_ZMQContext = zmq_ctx_new();
    m_ZMQSocket = zmq_socket(m_ZMQContext, ZMQ_SUB);

    // Subscribe to the {{ TEMPLATE }} PUB-SUB channel
    zmq_setsockopt(m_ZMQSocket, ZMQ_SUBSCRIBE, "{{ TEMPLATE }}", strlen("{{ TEMPLATE }}"));

    zmq_connect(m_ZMQSocket, "tcp://localhost:{{ ZMQ_SHELL_PORT }}");
} // end of {{ TEMPLATE }}::Init()

void {{ TEMPLATE }}::Cleanup(void) {
    zmq_close(m_ZMQSocket);
    zmq_ctx_destroy(m_ZMQContext);
} // end of {{ TEMPLATE }}::Cleanup()

void {{ TEMPLATE }}::ProcessZMQ(void) {
    zmq_msg_t msg;
    zmq_msg_init(&msg);

    if(zmq_recvmsg(m_ZMQSocket, &msg, ZMQ_DONTWAIT) == -1)
        return;

    msgpack::object_handle h = msgpack::unpack((char *)zmq_msg_data(&msg), zmq_msg_size(&msg));
    msgpack::object deserialized = h.get();
    msgpack::type::tuple<int, std::string> cmd;
    deserielized.convert(cmd);

    int msgType = std::get<0>(cmd);
    std::string objName = std::get<1><cmd);
    switch(msgType) {
        case MSG_TYPE_CREATE: {
            printf("Create {{ TEMPLATE }} %s\n", objName.c_str());
        } break;
        case MSG_TYPE_DELETE: {
            printf("Delete {{ TEMPLATE }} %s\n", objName.c_str());
        } break;
        case MSG_TYPE_MODIFY: {
            printf("Modify {{ TEMPLATE }} %s\n", objName.c_str());
        } break;
        case MSG_TYPE_ADD_REF: {
        } break;
        case MSG_TYPE_DELETE_REF: {
        } break;
        default:
        throw "Unknown message type";
    }
} // end of {{ TEMPLATE }}::ProcessZMQ()

class {{ TEMPLATE }} {

public:

private:

};