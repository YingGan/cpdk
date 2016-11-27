// 3rd party requirements
#include <zmq.h>
#include "json.hpp"

// Standard libraries
#include <stdio.h>
#include <string.h>
#include <cassert>
#include <unordered_map>

using json = nlohmann::json;

#define MSG_TYPE_CREATE 1
#define MSG_TYPE_DELETE 2
#define MSG_TYPE_MODIFY 3
#define MSG_TYPE_ADD_REF 4
#define MSG_TYPE_DELETE_REF 5

class {{ TEMPLATE_BASE }} {
public:
    {{ TEMPLATE_BASE }}(std::string name){m_Name = name;}
    virtual ~{{ TEMPLATE_BASE }}(){}

    {{ TEMPLATE_BASE_FIELDS }}

    inline std::string GetName(){return m_Name;}
private:
    std::string m_Name;
};

typedef {{ TEMPLATE_BASE }} * (*{{ TEMPLATE_BASE }}_Create)(std::string name, void *pData);
typedef void (*{{ TEMPLATE_BASE }}_Delete)({{ TEMPLATE_BASE }} *pObj, void *pData);

class {{ TEMPLATE_MGR }} {
public:
    void Init({{ TEMPLATE_BASE }}_Create create_cb, {{ TEMPLATE_BASE }}_Delete delete_cb, void *pData);
    void Cleanup(void);
    void ProcessMessageQueue(void);

    static {{ TEMPLATE_MGR }} & GetInstance() {
        static {{ TEMPLATE_MGR }} s_Instance;
        return s_Instance;
    }

private:
    void * m_ZMQPubSubSocket;
    void * m_ZMQContext;

    {{ TEMPLATE_BASE }}_Create m_CreateCallback;
    {{ TEMPLATE_BASE }}_Delete m_DeleteCallback;
    void * m_pCallbackData;

    std::unordered_map<std::string, {{ TEMPLATE_BASE }} *> m_InstanceMap;

protected:
    // Constructors (hidden for singleton-only access)
    {{ TEMPLATE_MGR }}() {};
    {{ TEMPLATE_MGR }}({{ TEMPLATE_MGR }} const &);
    void operator=({{ TEMPLATE_MGR }} const&);
};

void {{ TEMPLATE_MGR }}::Init({{ TEMPLATE_BASE }}_Create create_cb, {{ TEMPLATE_BASE }}_Delete delete_cb, void *pData) {

    m_CreateCallback = create_cb;
    m_DeleteCallback = delete_cb;
    m_pCallbackData = pData;

    m_ZMQContext = zmq_ctx_new();
    m_ZMQPubSubSocket = zmq_socket(m_ZMQContext, ZMQ_SUB);

    // Subscribe to the {{ TEMPLATE_BASE }} PUB-SUB channel
    zmq_setsockopt(m_ZMQPubSubSocket, ZMQ_SUBSCRIBE, "[\"{{ TEMPLATE_BASE }}\"", strlen("[\"{{ TEMPLATE_BASE }}\""));
    zmq_connect(m_ZMQPubSubSocket, "tcp://localhost:{{ ZMQ_PUBSUB_PORT }}");

    // Subscribe to the client-server socket
    void * clientSocket = zmq_socket(m_ZMQContext, ZMQ_REQ);
    zmq_connect(clientSocket, "tcp://localhost:{{ ZMQ_CLIENT_SERVER_PORT }}");
    json j;
    j["object"] = "{{ TEMPLATE_BASE }}";
    std::string j_msg = j.dump();
    zmq_send(clientSocket, j_msg.c_str(), strlen(j_msg.c_str()), 0);

    zmq_msg_t msg;
    zmq_msg_init(&msg);

    int msgLen = zmq_recvmsg(clientSocket, &msg, 0);
    if(msgLen == -1)
        // TODO: Something more meaningful
        throw "oops";

    std::string recvBuffer((char *)zmq_msg_data(&msg), msgLen);
    json j2 = json::parse(recvBuffer.c_str());

    for (json::iterator obj_it = j2.begin(); obj_it != j2.end(); ++obj_it) {
        {{ TEMPLATE_BASE }} *pObj = m_CreateCallback(obj_it.key(), m_pCallbackData);
        m_InstanceMap[obj_it.key()] = pObj;

        for (json::iterator it = obj_it.value().begin(); it != obj_it.value().end(); ++it) {
            std::string field = it.key();
            auto value = it.value();

            assert(value.is_null() == false);  // CPDKd shouldn't allow null values to get through
{{ TEMPLATE_BASE_MODIFY_LOGIC }}
        }
    }

    zmq_close(clientSocket);
} // end of {{ TEMPLATE_MGR }}::Init()

void {{ TEMPLATE_MGR }}::Cleanup(void) {
    zmq_close(m_ZMQPubSubSocket);
    zmq_ctx_destroy(m_ZMQContext);
} // end of {{ TEMPLATE_MGR }}::Cleanup()

void {{ TEMPLATE_MGR }}::ProcessMessageQueue(void) {
    zmq_msg_t msg;
    zmq_msg_init(&msg);

    // Process any messages from the PUB-SUB socket
    int msg_len = zmq_recvmsg(m_ZMQPubSubSocket, &msg, ZMQ_DONTWAIT);
    if( msg_len == -1)
        return;

    std::string recvBuffer((char *)zmq_msg_data(&msg), msg_len);
    json j = json::parse((char *)recvBuffer.c_str());
    json data = j.at(1);
    std::string objName = data["obj"];
    int id = data["type"];

    switch(id) {
        case MSG_TYPE_CREATE: {
            m_InstanceMap[objName] = m_CreateCallback(objName, NULL);
        } break;
        case MSG_TYPE_DELETE: {
            {{ TEMPLATE_BASE }} *pObj = m_InstanceMap[objName];
            m_InstanceMap.erase(pObj->GetName());
            m_DeleteCallback(pObj, NULL);
        } break;
        case MSG_TYPE_MODIFY: {
            {{ TEMPLATE_BASE }} *pObj = m_InstanceMap[objName];
            std::string field = data["field"];
            auto value = data["value"];

{{ TEMPLATE_BASE_MODIFY_LOGIC }}
        } break;
        case MSG_TYPE_ADD_REF: {
            throw "Not Implemented";
        } break;
        case MSG_TYPE_DELETE_REF: {
            throw "Not Implemented";
        } break;
        default:
        throw "Unknown message type";
    }
} // end of {{ TEMPLATE_MGR }}::ProcessMessageQueue()