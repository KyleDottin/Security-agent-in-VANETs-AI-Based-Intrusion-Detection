////To place in veins/src/veins/modules/application/traci/MyVeinsApp.cc
// Copyright (C) 2016 David Eckhoff <david.eckhoff@fau.de>
//
// Documentation for these modules is at http://veins.car2x.org/
//
// SPDX-License-Identifier: GPL-2.0-or-later
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//

#include "veins/modules/application/traci/MyVeinsApp.h"

using namespace veins;

Define_Module(veins::MyVeinsApp);

void MyVeinsApp::initialize(int stage)
{
    DemoBaseApplLayer::initialize(stage);
    if (stage == 0) {
        // Initialize TraCI components
        try {
            mobility = TraCIMobilityAccess().get(getParentModule());
            traci = mobility->getCommandInterface();
            traciVehicle = mobility->getVehicleCommandInterface();
            
            if (!mobility || !traci || !traciVehicle) {
                EV << "Error: Failed to initialize TraCI components" << endl;
                return;
            }
            
            EV << "\n=== VEHICLE INITIALIZED ===" << endl;
            EV << "ID: [" << getParentModule()->getFullName() << "]" << endl;
            EV << "=========================" << endl;
        } catch (std::exception& e) {
            EV << "Error in initialize: " << e.what() << endl;
        }
    }
}

void MyVeinsApp::finish()
{
    DemoBaseApplLayer::finish();
    try {
        EV << "\n=== VEHICLE FINISHED ===" << endl;
        EV << "ID: [" << getParentModule()->getFullName() << "]" << endl;
        EV << "TIME: " << simTime() << endl;
        EV << "=========================" << endl;
    } catch (std::exception& e) {
        EV << "Error in finish: " << e.what() << endl;
    }
}

void MyVeinsApp::onBSM(DemoSafetyMessage* bsm)
{
    if (!bsm) {
        EV << "Error: Received null BSM" << endl;
        return;
    }

    try {
        // Log received beacon message with clear separators
        EV << "\n=== BSM RECEIVED ===" << endl;
        EV << "RECEIVER: [" << getParentModule()->getFullName() << "]" << endl;
        
        // Get sender info safely
        cModule* senderMod = bsm->getSenderModule();
        if (senderMod) {
            EV << "SENDER: [" << senderMod->getFullName() << "]" << endl;
        } else {
            EV << "SENDER: Unknown" << endl;
        }

        // Get position info safely
        Coord senderPos = bsm->getSenderPos();
        EV << "SENDER POS: (" << senderPos.x << ", " << senderPos.y << ")" << endl;
        
        // Only calculate distance if we have valid position
        if (mobility && mobility->getPositionAt(simTime()).length() > 0) {
            curPosition = mobility->getPositionAt(simTime());
            EV << "DISTANCE: " << curPosition.distance(senderPos) << " m" << endl;
        }
        
        EV << "===================" << endl;
    } catch (std::exception& e) {
        EV << "Error in onBSM: " << e.what() << endl;
    }
}

void MyVeinsApp::onWSM(BaseFrame1609_4* wsm)
{
    if (!wsm) {
        EV << "Error: Received null WSM" << endl;
        return;
    }

    try {
        // Log received wireless message with clear separators
        EV << "\n=== WSM RECEIVED ===" << endl;
        EV << "RECEIVER: [" << getParentModule()->getFullName() << "]" << endl;
        EV << "MESSAGE: " << wsm->getName() << endl;
        EV << "TIME: " << simTime() << endl;

        DemoSafetyMessage* bsm = dynamic_cast<DemoSafetyMessage*>(wsm);
        if (bsm) {
            Coord senderPos = bsm->getSenderPos();
            EV << "SENDER POS: (" << senderPos.x << ", " << senderPos.y << ")" << endl;
            if (mobility) {
                curPosition = mobility->getPositionAt(simTime());
                EV << "DISTANCE: " << curPosition.distance(senderPos) << " m" << endl;
            }
        }
        EV << "===================" << endl;
    } catch (std::exception& e) {
        EV << "Error in onWSM: " << e.what() << endl;
    }
}

void MyVeinsApp::onWSA(DemoServiceAdvertisment* wsa)
{
    if (!wsa) {
        EV << "Error: Received null WSA" << endl;
        return;
    }

    try {
        EV << "\n=== WSA RECEIVED ===" << endl;
        EV << "RECEIVER: [" << getParentModule()->getFullName() << "]" << endl;
        EV << "SERVICE INFO: " << wsa->getServiceDescription() << endl;
        EV << "===================" << endl;
    } catch (std::exception& e) {
        EV << "Error in onWSA: " << e.what() << endl;
    }
}

void MyVeinsApp::handleSelfMsg(cMessage* msg)
{
    if (msg) {
        DemoBaseApplLayer::handleSelfMsg(msg);
    }
}

void MyVeinsApp::handlePositionUpdate(cObject* obj)
{
    DemoBaseApplLayer::handlePositionUpdate(obj);
    // Update current position
    if (mobility) {
        curPosition = mobility->getPositionAt(simTime());
    }
}
