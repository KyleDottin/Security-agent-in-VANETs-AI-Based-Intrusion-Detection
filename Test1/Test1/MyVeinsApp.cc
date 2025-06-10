//
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
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <list>
#include <stdint.h>
#include "veins/modules/mobility/traci/TraCIMobility.h"
#include "veins/modules/mobility/traci/TraCICommandInterface.h"
#include "veins/modules/application/traci/TraCIDemo11p.h"
#include "veins/modules/application/traci/TraCIDemo11pMessage_m.h"
#include "veins/modules/application/traci/TraCIDemo11p.h"



using namespace veins;

Define_Module(veins::MyVeinsApp);

void MyVeinsApp::initialize(int stage)
{
    DemoBaseApplLayer::initialize(stage);
    if (stage == 0) {
        // Initializing members and pointers of your application goes here
        EV << "Initializing " << par("appName").stringValue() << std::endl;
        //mobility = TraCIMobilityAccess().get(getParentModule());
        //traci = mobility->getCommandInterface();
        //traciVehicle = mobility->getVehicleCommandInterface();
        // Schedule a self-message to periodically retrieve vehicle data

    }
    else if (stage == 1) {
        // Initializing members that require initialized other modules goes here
    }
}

void MyVeinsApp::finish()
{
    DemoBaseApplLayer::finish();
    // statistics recording goes here
}




void MyVeinsApp::onBSM(DemoSafetyMessage* bsm)
{
    // Your application has received a beacon message from another car or RSU
    // code for handling the message goes here
    //traciSimulation->getTime();


    std::string laneId = traciVehicle->getLaneId();
    double speed = traciVehicle->getSpeed();

    //traciVehicle->getIDList();
    std::cout << "lane: " << laneId << std::endl;
    std::cout << "Speed: " << speed << std::endl;

    //traci->trafficlight();

    std::string command = "python3 sum.py " + std::to_string(speed) + " 3";
    system(command.c_str());

    //system("python3 sum.py 5 3");
    // Read the result file
    std::ifstream infile("result.txt");
    std::string result;
    infile >> result;
    std::cout << "Python result: " << result << std::endl;
    int sum = std::stoi(result);  // Convert to integer
    std::cout << "Sum as integer: " << sum << std::endl;

    // Optional: Delete the temporary file
    remove("result.txt");
    //EV << "Sum: " << sum << std::endl;
    //EV << "Done" << std::endl;

    traciVehicle->setSpeed(sum);

}





void MyVeinsApp::onWSM(BaseFrame1609_4* wsm)
{
    // Your application has received a data message from another car or RSU
    // code for handling the message goes here, see TraciDemo11p.cc for examples
    // Get the list of vehicle IDs

}

void MyVeinsApp::onWSA(DemoServiceAdvertisment* wsa)
{
    // Your application has received a service advertisement from another car or RSU
    // code for handling the message goes here, see TraciDemo11p.cc for examples
}

void MyVeinsApp::handleSelfMsg(cMessage* msg)
{
    DemoBaseApplLayer::handleSelfMsg(msg);
    // this method is for self messages (mostly timers)
    // it is important to call the DemoBaseApplLayer function for BSM and WSM transmission
}



void MyVeinsApp::handlePositionUpdate(cObject* obj)
{
    DemoBaseApplLayer::handlePositionUpdate(obj);
    // the vehicle has moved. Code that reacts to new positions goes here.
    // member variables such as currentPosition and currentSpeed are updated in the parent class


}
