#pragma once

#include "veins/veins.h"

#include "veins/modules/application/ieee80211p/DemoBaseApplLayer.h"
#include "veins/modules/messages/BaseFrame1609_4_m.h"
#include "veins/modules/messages/DemoSafetyMessage_m.h"

#include "veins/modules/mobility/traci/TraCIMobility.h"
#include "veins/modules/mobility/traci/TraCICommandInterface.h"

#include <fstream>
#ifdef _WIN32
    #include <winsock2.h> // For Windows
    #include <ws2tcpip.h>
#else
    #include <netinet/in.h> // For linux
    #include <arpa/inet.h>
#endif
#include <string>

using namespace omnetpp;

namespace veins {

/**
 * @brief
 * This is a stub for a typical Veins application layer.
 * Most common functions are overloaded.
 * See MyVeinsApp.cc for hints
 *
 * @author David Eckhoff
 *
 */

class VEINS_API MyVeinsApp : public DemoBaseApplLayer {
public:
    void initialize(int stage) override;
    void finish() override;

protected:
    void onBSM(DemoSafetyMessage* bsm) override;
    void onWSM(BaseFrame1609_4* wsm) override;
    void onWSA(DemoServiceAdvertisment* wsa) override;

    void handleSelfMsg(cMessage* msg) override;
    void handlePositionUpdate(cObject* obj) override;

    void handleEmergencyMessage(BaseFrame1609_4* wsm);
    void handleTrafficInfo(BaseFrame1609_4* wsm);
    void logReceivedMessage(const std::string& senderId, const std::string& data,
                           simtime_t timestamp, double distance);
    bool shouldReply(BaseFrame1609_4* wsm);
    void sendReply(const std::string& originalSenderId);

    // === New Methods and Members for Python UDP Communication ===
    void initializeUDPSocket();
    void sendToPython(const std::string& message);

    int udpSocket = -1;
    struct sockaddr_in pythonAddr;

    Coord curPosition;

    // TraCI interfaces
    veins::TraCIMobility* mobility = nullptr;
    veins::TraCICommandInterface* traci = nullptr;
    veins::TraCICommandInterface::Vehicle* traciVehicle = nullptr;
};

} // namespace veins
