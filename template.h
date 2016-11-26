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
    ~{{ TEMPLATE_BASE }}(){}

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
    void * m_ZMQSocket;
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
    m_ZMQSocket = zmq_socket(m_ZMQContext, ZMQ_SUB);

    // Subscribe to the {{ TEMPLATE_BASE }} PUB-SUB channel
    zmq_setsockopt(m_ZMQSocket, ZMQ_SUBSCRIBE, "[\"{{ TEMPLATE_BASE }}\"", strlen("[\"{{ TEMPLATE_BASE }}\""));
    zmq_connect(m_ZMQSocket, "tcp://localhost:{{ ZMQ_PUBSUB_PORT }}");
} // end of {{ TEMPLATE_MGR }}::Init()

void {{ TEMPLATE_MGR }}::Cleanup(void) {
    zmq_close(m_ZMQSocket);
    zmq_ctx_destroy(m_ZMQContext);
} // end of {{ TEMPLATE_MGR }}::Cleanup()

void {{ TEMPLATE_MGR }}::ProcessMessageQueue(void) {
    zmq_msg_t msg;
    zmq_msg_init(&msg);

    if(zmq_recvmsg(m_ZMQSocket, &msg, ZMQ_DONTWAIT) == -1)
        return;

    json j = json::parse((char *)zmq_msg_data(&msg));
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

        } break;
        case MSG_TYPE_ADD_REF: {
        } break;
        case MSG_TYPE_DELETE_REF: {
        } break;
        default:
        throw "Unknown message type";
    }
} // end of {{ TEMPLATE_MGR }}::ProcessMessageQueue()