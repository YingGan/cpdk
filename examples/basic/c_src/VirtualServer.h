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
#define MSG_TYPE_DELETE_ALL 6

// Forward declarations
class Server;
class ServerMgr;


class VirtualServer {
public:
    VirtualServer(std::string name){m_Name = name;}
    virtual ~VirtualServer(){}

    virtual void on_add_Server(std::string name) { }
virtual void on_remove_Server(std::string name) { }


    virtual void on_id(int val) { }
virtual void on_name(std::string val) { }
virtual void on_address(std::string val) { }
virtual void on_port(int val) { }
virtual void on_enabled(bool val) { }


    inline std::string GetName(){return m_Name;}
private:
    std::string m_Name;
};

typedef VirtualServer * (*VirtualServer_Create)(std::string name, void *pData);
typedef void (*VirtualServer_Delete)(VirtualServer *pObj, void *pData);

class VirtualServerMgr {
public:

    static VirtualServerMgr & GetInstance() {
        static VirtualServerMgr s_Instance;
        return s_Instance;
    }

    void Init(VirtualServer_Create create_cb, VirtualServer_Delete delete_cb, void *pData);
    void Cleanup(void);
    void ProcessMessageQueue(void);
    VirtualServer * GetObj(std::string name){ return m_InstanceMap[name];}

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

    VirtualServer_Create m_CreateCallback;
    VirtualServer_Delete m_DeleteCallback;
    void * m_pCallbackData;

    typedef std::unordered_map<std::string, VirtualServer *> ObjMap;
    ObjMap m_InstanceMap;

    json SendClientMessage(json &j);

protected:
    // Constructors (hidden for singleton-only access)
    VirtualServerMgr() {};
    VirtualServerMgr(VirtualServerMgr const &);
    void operator=(VirtualServerMgr const&);
};

void VirtualServerMgr::Init(VirtualServer_Create create_cb, VirtualServer_Delete delete_cb, void *pData) {

    m_CreateCallback = create_cb;
    m_DeleteCallback = delete_cb;
    m_pCallbackData = pData;

    m_ZMQContext = zmq_ctx_new();
    m_ZMQPubSubSocket = zmq_socket(m_ZMQContext, ZMQ_SUB);

    // Subscribe to the VirtualServer PUB-SUB channel
    zmq_setsockopt(m_ZMQPubSubSocket, ZMQ_SUBSCRIBE, "[\"VirtualServer\"", strlen("[\"VirtualServer\""));
    zmq_connect(m_ZMQPubSubSocket, "tcp://localhost:5744");

    // Subscribe to the client-server socket
    m_ZMQClientSocket = zmq_socket(m_ZMQContext, ZMQ_REQ);
    zmq_connect(m_ZMQClientSocket, "tcp://localhost:5279");

    // Fetch all of the objects this manager cares about
    json j;
    j["t"] = "list";
    j["o"] = "VirtualServer";
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
        VirtualServer *pObj = m_CreateCallback(obj["name"], m_pCallbackData);
        m_InstanceMap[obj["name"]] = pObj;

        for (json::iterator it = obj.begin(); it != obj.end(); ++it) {
            std::string field = it.key();
            auto value = it.value();

            if(value.is_null())
                continue;
if(field == "id") {
    pObj->on_id(value);
} else if(field == "name") {
    pObj->on_name(value);
} else if(field == "address") {
    pObj->on_address(value);
} else if(field == "port") {
    pObj->on_port(value);
} else if(field == "enabled") {
    pObj->on_enabled(value);
} 

if(field == "servers") {
   for(auto &obj : value) {
      pObj->on_add_Server(obj);
   }
}

        }
    }


} // end of VirtualServerMgr::Init()

void VirtualServerMgr::Cleanup(void) {
    zmq_close(m_ZMQPubSubSocket);
    zmq_close(m_ZMQClientSocket);
    zmq_ctx_destroy(m_ZMQContext);
} // end of VirtualServerMgr::Cleanup()

void VirtualServerMgr::DeleteAll(void) {
    json j;
    j["t"] = "delete_all";
    j["o"] = "VirtualServer";
    SendClientMessage(j);

    // Note: No actual deletes will occur here.
    //  CPDKd will send us a "delete all" message on the pub-sub channel.
} // end of void VirtualServerMgr::DeleteAll()

void VirtualServerMgr::Create(std::string objectName) {
    json j;
    j["t"] = "create";
    j["o"] = "VirtualServer";
    j["on"] = objectName;

    SendClientMessage(j);

    // Note: No actual creates will occur here.
    //  CPDKd will send us a "create" message on the pub-sub channel.

} // end of VirtualServerMgr::Create()

json VirtualServerMgr::SendClientMessage(json &j) {

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
} // end of VirtualServerMgr::SendClientMessage()

void VirtualServerMgr::UpdateField(std::string objectName, std::string fieldName, std::string val) {
    json j;
    j["t"] = "modify";
    j["o"] = "VirtualServer";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of VirtualServerMgr::UpdateField()

void VirtualServerMgr::UpdateField(std::string objectName, std::string fieldName, uint64_t val) {
    json j;
    j["t"] = "modify";
    j["o"] = "VirtualServer";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of VirtualServerMgr::UpdateField()

void VirtualServerMgr::UpdateField(std::string objectName, std::string fieldName, bool val) {
    json j;
    j["t"] = "modify";
    j["o"] = "VirtualServer";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of VirtualServerMgr::UpdateField()


void VirtualServerMgr::ProcessMessageQueue(void) {
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
                VirtualServer *pObj = m_InstanceMap[objName];
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

            VirtualServer *pObj = m_InstanceMap[objName];
            std::string field = data["field"];
            auto value = data["value"];

if(field == "id") {
    pObj->on_id(value);
} else if(field == "name") {
    pObj->on_name(value);
} else if(field == "address") {
    pObj->on_address(value);
} else if(field == "port") {
    pObj->on_port(value);
} else if(field == "enabled") {
    pObj->on_enabled(value);
} 

        } break;
        case MSG_TYPE_ADD_REF: {
            ObjMap::iterator it = m_InstanceMap.find(objName);
            assert(it != m_InstanceMap.end());

            VirtualServer *pObj = it->second;
            std::string field = data["field"];
            auto value = data["value"];

            if(field == "Server") {
    pObj->on_add_Server(value);
}

        } break;
        case MSG_TYPE_DELETE_REF: {
            ObjMap::iterator it = m_InstanceMap.find(objName);
            assert(it != m_InstanceMap.end());

            VirtualServer *pObj = it->second;
            std::string field = data["field"];
            auto value = data["value"];

            if(field == "Server") {
    pObj->on_remove_Server(value);
}

        } break;
        default:
        throw "Unknown message type";
    }
} // end of VirtualServerMgr::ProcessMessageQueue()