#include "Server.h"
#include "Interface.h"
#include <unistd.h>


// Custom server class. Instantiated by the Server object manager.
class MyServer : public Server {
public:
    inline MyServer(std::string name) : Server(name) {}
    virtual void on_something(int val);
};

// Get notified when the user changes the 'something' parameter
void MyServer::on_something(int val) {

    std::cout << this->GetName() << ":" << val << std::endl;
}

// Callbacks for creating and deleting servers
Server * CreateCallback(std::string name, void *pData) {
    std::cout << "In CreateCallback for " << name << std::endl;
    return new MyServer(name);
}

void DeleteCallback(Server *pServer, void *pData) {
    std::cout << "In DeleteCallback for " << pServer->GetName() << std::endl;
    delete pServer;
}

// Callbacks for creating and deleting interfaces
Interface * CreateInterfaceCB(std::string name, void *pData) {
    std::cout << "In CreateCallback for " << name << std::endl;
    return new Interface(name);
}

void DeleteInterfaceCB(Interface *pInterface, void *pData) {
    std::cout << "In DeleteCallback for " << pInterface->GetName() << std::endl;
    delete pInterface;
}

// Global running variable. Set to false when user hits ctrl-c
bool is_running = true;

void sig_handler(int sig) {
    is_running = false;
} // end of sig_handler()

int main(void) {

    // Register a signal handler to process ctrl-c
    signal(SIGINT, sig_handler);

    // Initialize our object managers
    ServerMgr::GetInstance().Init(CreateCallback, DeleteCallback, NULL);
    InterfaceMgr::GetInstance().Init(CreateInterfaceCB, DeleteInterfaceCB, NULL);

    // Delete any existing interface objectsin the database
    InterfaceMgr::GetInstance().DeleteAll();

    // Create an interface object
    InterfaceMgr::GetInstance().Create("eth12");
    InterfaceMgr::GetInstance().UpdateField("eth12", "packets_in", uint64_t(123));
    InterfaceMgr::GetInstance().UpdateField("eth12", "packets_out", uint64_t(456));
    InterfaceMgr::GetInstance().UpdateField("eth12", "enabled", true);

    // Enter the main message processing loop
    while(is_running) {
        ServerMgr::GetInstance().ProcessMessageQueue();
        InterfaceMgr::GetInstance().ProcessMessageQueue();
    }

    std::cout << "exiting..." << std::endl;

    // Delete any daemon-managed objects.
    InterfaceMgr::GetInstance().DeleteAll();

    // Allow the object managers to cleanup
    ServerMgr::GetInstance().Cleanup();
    InterfaceMgr::GetInstance().Cleanup();
    return 0;
} // end of main()
