package veins.examples;

import veins.nodes.BaseWaveApplLayer;
import veins.nodes.Vehicle;

network SimpleScenarioNoTraCI
{
    parameters:
        @display("bgb=800,400");
    submodules:
        car[2]: Vehicle {
            parameters:
                @display("i=vehicle/van;p=100+200*i,150");
        }
}
