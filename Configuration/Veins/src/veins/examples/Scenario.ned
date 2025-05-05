package veins.examples;

import veins.modules.mobility.traci.TraCIScenarioManagerLaunch;
import veins.nodes.Vehicle;

network Scenario {
    parameters:
        @display("bgb=600,400");
    submodules:
        manager: TraCIScenarioManagerLaunch {
            parameters:
                @display("p=100,100");
        }
        car[1]: Vehicle {
            parameters:
                @display("p=200,200");
        }
}
