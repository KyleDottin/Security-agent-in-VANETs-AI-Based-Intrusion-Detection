energy = 0
CO = 0
CO2 = 0
NVMOC = 0
NOx	= 0
PM	= 0

def fuel_consumption():
    global energy, CO, CO2, NVMOC, NOx, PM
    if traci.vehicle.getIDCount() !=0:
        for id in traci.vehicle.getIDList():
            if traci.vehicle.getSpeed(id)>0:
                energy += traci.vehicle.getFuelConsumption(id)/1000
            else:
                energy += 0.25
    CO = 84.7 * (energy/1000)
    CO2 = 3.18 * (energy/1000)
    NVMOC = 10.05 * (energy/1000)
    NOx	= 8.73 * (energy/1000)
    PM	= 0.03 * (energy/1000)