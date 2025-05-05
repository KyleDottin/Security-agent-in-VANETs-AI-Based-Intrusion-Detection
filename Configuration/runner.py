
import traci

sumoBinary= "/home/veins/src/sumo/bin/sumo"
sumoCmd = [sumoBinary,"-c",
           "Security-agent-in-VANETs-AI-Based-Intrusion-Detection/Configuration/Veins/src/Basic.sumo.cfg"]

traci.start(sumoCmd)

