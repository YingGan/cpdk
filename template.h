// 3rd party requirements
#include "zmq.h"
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
#define MSG_TYPE_DELETE_ALL 6

{{ TEMPLATE_FORWARD_DECLS }}

class {{ TEMPLATE_BASE }} {
public:
    {{ TEMPLATE_BASE }}(std::string name){m_Name = name;}
    virtual ~{{ TEMPLATE_BASE }}(){}

    {{ TEMPLATE_REFERENCE_FIELDS }}

    {{ TEMPLATE_BASE_FIELDS }}

    inline std::string GetName(){return m_Name;}
private:
    std::string m_Name;
};

typedef {{ TEMPLATE_BASE }} * (*{{ TEMPLATE_BASE }}_Create)(std::string name, void *pData);
typedef void (*{{ TEMPLATE_BASE }}_Delete)({{ TEMPLATE_BASE }} *pObj, void *pData);

class {{ TEMPLATE_MGR }} {
public:

    static {{ TEMPLATE_MGR }} & GetInstance() {
        static {{ TEMPLATE_MGR }} s_Instance;
        return s_Instance;
    }

    void Init({{ TEMPLATE_BASE }}_Create create_cb, {{ TEMPLATE_BASE }}_Delete delete_cb, void *pData);
    void Cleanup(void);
    void ProcessMessageQueue(void);
    {{ TEMPLATE_BASE }} * GetObj(std::string name){ return m_InstanceMap[name];}

    // Methods for object management
    void DeleteAll(void);
    void Create(std::string objectName);
    void UpdateField(std::string objectName, std::string fieldName, std::string val);
    void UpdateField(std::string objectName, std::string fieldName, uint64_t val);
    void UpdateField(std::string objectName, std::string fieldName, bool val);
    // TODO: Add more data types to UpdateField()

private:
    void * m_ZMQPubSubSocket;
    void * m_ZMQClientSocket;
    void * m_ZMQContext;

    {{ TEMPLATE_BASE }}_Create m_CreateCallback;
    {{ TEMPLATE_BASE }}_Delete m_DeleteCallback;
    void * m_pCallbackData;

    typedef std::unordered_map<std::string, {{ TEMPLATE_BASE }} *> ObjMap;
    ObjMap m_InstanceMap;

    json SendClientMessage(json &j);

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
    m_ZMQClientSocket = zmq_socket(m_ZMQContext, ZMQ_REQ);
    zmq_connect(m_ZMQClientSocket, "tcp://localhost:{{ ZMQ_CLIENT_SERVER_PORT }}");

    // Fetch all of the objects this manager cares about
    json j;
    j["t"] = "list";
    j["o"] = "{{ TEMPLATE_BASE }}";
    std::string j_msg = j.dump();
    zmq_send(m_ZMQClientSocket, j_msg.c_str(), strlen(j_msg.c_str()), 0);

    zmq_msg_t msg;
    zmq_msg_init(&msg);

    int msgLen = zmq_recvmsg(m_ZMQClientSocket, &msg, 0);
    if(msgLen == -1)
        // TODO: Something more meaningful
        throw "oops";

    std::string recvBuffer((char *)zmq_msg_data(&msg), msgLen);
    json j2 = json::parse(recvBuffer.c_str());

    if(j2["status"] != "ok")
        // TODO: Needs a custom exception
        throw "list command failed";

    for(auto &obj : j2["result"]) {
        {{ TEMPLATE_BASE }} *pObj = m_CreateCallback(obj["name"], m_pCallbackData);
        m_InstanceMap[obj["name"]] = pObj;

        for (json::iterator it = obj.begin(); it != obj.end(); ++it) {
            std::string field = it.key();
            auto value = it.value();

            if(value.is_null())
                continue;
{{ TEMPLATE_BASE_MODIFY_LOGIC }}
{{ TEMPLATE_BASE_REF_INIT_LOGIC }}
        }
    }


} // end of {{ TEMPLATE_MGR }}::Init()

void {{ TEMPLATE_MGR }}::Cleanup(void) {
    zmq_close(m_ZMQPubSubSocket);
    zmq_close(m_ZMQClientSocket);
    zmq_ctx_destroy(m_ZMQContext);
} // end of {{ TEMPLATE_MGR }}::Cleanup()

void {{ TEMPLATE_MGR }}::DeleteAll(void) {
    json j;
    j["t"] = "delete_all";
    j["o"] = "{{ TEMPLATE_BASE }}";
    SendClientMessage(j);

    // Note: No actual deletes will occur here.
    //  CPDKd will send us a "delete all" message on the pub-sub channel.
} // end of void {{ TEMPLATE_MGR }}::DeleteAll()

void {{ TEMPLATE_MGR }}::Create(std::string objectName) {
    json j;
    j["t"] = "create";
    j["o"] = "{{ TEMPLATE_BASE }}";
    j["on"] = objectName;

    SendClientMessage(j);

    // Note: No actual creates will occur here.
    //  CPDKd will send us a "create" message on the pub-sub channel.

} // end of {{ TEMPLATE_MGR }}::Create()

json {{ TEMPLATE_MGR }}::SendClientMessage(json &j) {

    int msgLen;
    zmq_msg_t msg;
    json jResponse;
    std::string j_msg;

    j_msg = j.dump();
    zmq_msg_init(&msg);

    zmq_send(m_ZMQClientSocket, j_msg.c_str(), strlen(j_msg.c_str()), 0);
    msgLen = zmq_recvmsg(m_ZMQClientSocket, &msg, 0);
    if(msgLen == -1)
        // TODO: Something more meaningful
        throw "oops";

    std::string recvBuffer((char *)zmq_msg_data(&msg), msgLen);
    jResponse = json::parse(recvBuffer.c_str());
    if(jResponse["status"] != "ok")
        // TODO: Needs a custom exception
        throw "list command failed";

    return jResponse;
} // end of {{ TEMPLATE_MGR }}::SendClientMessage()

void {{ TEMPLATE_MGR }}::UpdateField(std::string objectName, std::string fieldName, std::string val) {
    json j;
    j["t"] = "modify";
    j["o"] = "{{ TEMPLATE_BASE }}";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of {{ TEMPLATE_MGR }}::UpdateField()

void {{ TEMPLATE_MGR }}::UpdateField(std::string objectName, std::string fieldName, uint64_t val) {
    json j;
    j["t"] = "modify";
    j["o"] = "{{ TEMPLATE_BASE }}";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of {{ TEMPLATE_MGR }}::UpdateField()

void {{ TEMPLATE_MGR }}::UpdateField(std::string objectName, std::string fieldName, bool val) {
    json j;
    j["t"] = "modify";
    j["o"] = "{{ TEMPLATE_BASE }}";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of {{ TEMPLATE_MGR }}::UpdateField()


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

    std::string objName = "";
    if(data.find("obj") != data.end())   // Optional for messages like "DELETE_ALL"
        objName = data["obj"];

    int id = data["type"];

    switch(id) {
        case MSG_TYPE_CREATE: {
            m_InstanceMap[objName] = m_CreateCallback(objName, NULL);
        } break;
        case MSG_TYPE_DELETE: {
            ObjMap::iterator it = m_InstanceMap.find(objName);
            if(it != m_InstanceMap.end()) {
                {{ TEMPLATE_BASE }} *pObj = m_InstanceMap[objName];
                m_InstanceMap.erase(pObj->GetName());
                m_DeleteCallback(pObj, NULL);
            }
        } break;
        case MSG_TYPE_DELETE_ALL: {
            for(auto &it : m_InstanceMap) {
                m_DeleteCallback(it.second, NULL);
            }
            m_InstanceMap.clear();
        } break;
        case MSG_TYPE_MODIFY: {
            ObjMap::iterator it = m_InstanceMap.find(objName);
            if(it == m_InstanceMap.end())
                break;

            {{ TEMPLATE_BASE }} *pObj = m_InstanceMap[objName];
            std::string field = data["field"];
            auto value = data["value"];

{{ TEMPLATE_BASE_MODIFY_LOGIC }}
        } break;
        case MSG_TYPE_ADD_REF: {
            ObjMap::iterator it = m_InstanceMap.find(objName);
            assert(it != m_InstanceMap.end());

            {{ TEMPLATE_BASE }} *pObj = it->second;
            std::string field = data["field"];
            auto value = data["value"];

            {{ TEMPLATE_BASE_REF_ADD_LOGIC }}
            pObj = NULL; // Prevent compiler warnings
        } break;
        case MSG_TYPE_DELETE_REF: {
            ObjMap::iterator it = m_InstanceMap.find(objName);
            assert(it != m_InstanceMap.end());

            {{ TEMPLATE_BASE }} *pObj = it->second;
            std::string field = data["field"];
            auto value = data["value"];

            {{ TEMPLATE_BASE_REF_DELETE_LOGIC }}
            pObj = NULL; // Prevent compiler warnings
        } break;
        default:
        throw "Unknown message type";
    }
} // end of {{ TEMPLATE_MGR }}::ProcessMessageQueue()