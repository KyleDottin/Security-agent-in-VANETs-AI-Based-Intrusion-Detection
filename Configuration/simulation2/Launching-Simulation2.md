# Launching `simulation2`

To run the simulation, follow these steps from a Linux terminal:

## 1. Set the SUMO environment variable
```bash
export SUMO_HOME=/usr/share/sumo
```

## 2. Verify the environment variable
You can check that it's correctly set with:
```bash
echo $SUMO_HOME
```

## 3. Launch the simulation
Run the Python script:
```bash
python3 Traci.py
```

This will automatically start **SUMO**, run the simulation, and allow you to retrieve the vehicle's speed. Also, the vehicle 1 will stop for 3 seconds.
