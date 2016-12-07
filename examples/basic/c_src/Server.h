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
class VirtualServer;
class VirtualServerMgr;


class Server {
public:
    Server(std::string name){m_Name = name;}
    virtual ~Server(){}

    virtual void on_add_VirtualServer(std::string name) { }
virtual void on_remove_VirtualServer(std::string name) { }


    virtual void on_id(int val) { }
virtual void on_name(std::string val) { }
virtual void on_address(std::string val) { }
virtual void on_port(int val) { }
virtual void on_enabled(bool val) { }


    inline std::string GetName(){return m_Name;}
private:
    std::string m_Name;
};

typedef Server * (*Server_Create)(std::string name, void *pData);
typedef void (*Server_Delete)(Server *pObj, void *pData);

class ServerMgr {
public:

    static ServerMgr & GetInstance() {
        static ServerMgr s_Instance;
        return s_Instance;
    }

    void Init(Server_Create create_cb, Server_Delete delete_cb, void *pData);
    void Cleanup(void);
    void ProcessMessageQueue(void);
    Server * GetObj(std::string name){ return m_InstanceMap[name];}

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

    Server_Create m_CreateCallback;
    Server_Delete m_DeleteCallback;
    void * m_pCallbackData;

    typedef std::unordered_map<std::string, Server *> ObjMap;
    ObjMap m_InstanceMap;

    json SendClientMessage(json &j);

protected:
    // Constructors (hidden for singleton-only access)
    ServerMgr() {};
    ServerMgr(ServerMgr const &);
    void operator=(ServerMgr const&);
};

void ServerMgr::Init(Server_Create create_cb, Server_Delete delete_cb, void *pData) {

    m_CreateCallback = create_cb;
    m_DeleteCallback = delete_cb;
    m_pCallbackData = pData;

    m_ZMQContext = zmq_ctx_new();
    m_ZMQPubSubSocket = zmq_socket(m_ZMQContext, ZMQ_SUB);

    // Subscribe to the Server PUB-SUB channel
    zmq_setsockopt(m_ZMQPubSubSocket, ZMQ_SUBSCRIBE, "[\"Server\"", strlen("[\"Server\""));
    zmq_connect(m_ZMQPubSubSocket, "tcp://localhost:5744");

    // Subscribe to the client-server socket
    m_ZMQClientSocket = zmq_socket(m_ZMQContext, ZMQ_REQ);
    zmq_connect(m_ZMQClientSocket, "tcp://localhost:5279");

    // Fetch all of the objects this manager cares about
    json j;
    j["t"] = "list";
    j["o"] = "Server";
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
        Server *pObj = m_CreateCallback(obj["name"], m_pCallbackData);
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

if(field == "virtual_servers") {
   for(auto &obj : value) {
      pObj->on_add_VirtualServer(obj);
   }
}

        }
    }


} // end of ServerMgr::Init()

void ServerMgr::Cleanup(void) {
    zmq_close(m_ZMQPubSubSocket);
    zmq_close(m_ZMQClientSocket);
    zmq_ctx_destroy(m_ZMQContext);
} // end of ServerMgr::Cleanup()

void ServerMgr::DeleteAll(void) {
    json j;
    j["t"] = "delete_all";
    j["o"] = "Server";
    SendClientMessage(j);

    // Note: No actual deletes will occur here.
    //  CPDKd will send us a "delete all" message on the pub-sub channel.
} // end of void ServerMgr::DeleteAll()

void ServerMgr::Create(std::string objectName) {
    json j;
    j["t"] = "create";
    j["o"] = "Server";
    j["on"] = objectName;

    SendClientMessage(j);

    // Note: No actual creates will occur here.
    //  CPDKd will send us a "create" message on the pub-sub channel.

} // end of ServerMgr::Create()

json ServerMgr::SendClientMessage(json &j) {

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
} // end of ServerMgr::SendClientMessage()

void ServerMgr::UpdateField(std::string objectName, std::string fieldName, std::string val) {
    json j;
    j["t"] = "modify";
    j["o"] = "Server";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of ServerMgr::UpdateField()

void ServerMgr::UpdateField(std::string objectName, std::string fieldName, uint64_t val) {
    json j;
    j["t"] = "modify";
    j["o"] = "Server";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of ServerMgr::UpdateField()

void ServerMgr::UpdateField(std::string objectName, std::string fieldName, bool val) {
    json j;
    j["t"] = "modify";
    j["o"] = "Server";
    j["on"] = objectName;
    j["f"] = fieldName;
    j["fv"] = val;

    SendClientMessage(j);
} // end of ServerMgr::UpdateField()


void ServerMgr::ProcessMessageQueue(void) {
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
                Server *pObj = m_InstanceMap[objName];
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

            Server *pObj = m_InstanceMap[objName];
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

            Server *pObj = it->second;
            std::string field = data["field"];
            auto value = data["value"];

            if(field == "VirtualServer") {
    pObj->on_add_VirtualServer(value);
}

            pObj = NULL; // Prevent compiler warnings
        } break;
        case MSG_TYPE_DELETE_REF: {
            ObjMap::iterator it = m_InstanceMap.find(objName);
            assert(it != m_InstanceMap.end());

            Server *pObj = it->second;
            std::string field = data["field"];
            auto value = data["value"];

            if(field == "VirtualServer") {
    pObj->on_remove_VirtualServer(value);
}

            pObj = NULL; // Prevent compiler warnings
        } break;
        default:
        throw "Unknown message type";
    }
} // end of ServerMgr::ProcessMessageQueue()