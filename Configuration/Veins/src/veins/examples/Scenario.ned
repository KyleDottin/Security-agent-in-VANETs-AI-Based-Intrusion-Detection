package veins.examples;

import veins.modules.mobility.traci.TraCIScenarioManagerLaunchd;

network SimpleScenario
{
    submodules:
        manager: TraCIScenarioManagerLaunchd {
            parameters:
                @display("p=100,100");
        }
}
