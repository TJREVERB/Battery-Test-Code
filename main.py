from eps import EPS
from battery import Battery
import time

FETPDM = 7 # MOSFET PDM 7, when on the battery is charged by simulated solar panels
LOADPDM = 1 # Load PDM 1, when on the battery is discharged by electronic load

print("Initializing EPS + Battery")
eps = EPS()
battery = Battery()
print("Success")
chargeWh = 0 # Zero point is the start charge. Make sure battery is fully discharged before beginning.
chargeAh = 0

print("Initializing PDM pins")
eps.commands["Pin Init On"](FETPDM)
eps.commands["Pin Init Off"](LOADPDM) # Set initial states so that battery doesn't discharge itself if eps resets

eps.commands["All Off"]() # Ensure all PDMs are off first
print("Success")

print("Initializing log file")
filename = "CycleLog.csv"
log = open(filename, "w")
log.write("Charge (Wh),Charge (Ah),Voltage,Current,Time,TBAT1,TBAT2,TBAT3,TBAT4,TBRD,Cycle Number,Charge direction (chg/hold/dschg)\n")
log.close()
print("Success")

EOC = 8.185 # Set end of charge and end of discharge voltages
EODC = 6.4
time.sleep(5)

try:
    print(f"Discharging to End of Discharge Voltage {time.perf_counter()}")
    while battery.telemetry["VBAT"]() > EODC:
        time.sleep(.5)
        eps.commands["Pin On"](LOADPDM) # Turn on the load until battery is fully discharged
        time.sleep(.5)
    print(f"Discharge Complete {time.perf_counter()}")

    charging = True # Charging or discharging
    eps.commands["Pin Off"](LOADPDM) # Configure for charge
    eps.commands["Pin On"](FETPDM)
    lastpolltime = time.perf_counter()
    cycle = 0
    while cycle < 6:
        v, i, tbat1, tbat2, tbat3, tbat4, tbrd = battery.telem_summary() # Collect all telemetry at once
        recordtime = time.perf_counter()
        chargeWh += v * i * (recordtime - lastpolltime) / 3600
        chargeAh += i * (recordtime - lastpolltime) / 3600
        lastpolltime = recordtime
        #print(f"{chargeWh}, {chargeAh}, {v}, {i}, {recordtime}, {tbat1}, {tbat2}, {tbat3}, {tbat4}, {tbrd}, {cycle}")
        log = open(filename, "a")
        if charging:
            log.write(f"{chargeWh},{chargeAh},{v},{i},{recordtime},{tbat1},{tbat2},{tbat3},{tbat4},{tbrd},{cycle},chg\n")
        else:
            log.write(f"{chargeWh},{chargeAh},{v},{i},{recordtime},{tbat1},{tbat2},{tbat3},{tbat4},{tbrd},{cycle},dschg\n")
        log.close()

        eps.commands["Reset Watchdog"]() # Ping EPS to avoid reset

        if charging and v > EOC: # EPS Min value of EOC voltage
            if abs(i) < 0.05: # Battery termination current 50mA
                tstart = time.perf_counter()
                print(f"Charge Finished, {chargeWh} Wh")
                print(f"Beginning Charge Hold {tstart}")
                while time.perf_counter() - tstart < 60 * 10: # Wait for ten minutes, pinging battery and eps for telemetry in the mean time
                    time.sleep(.5)
                    v, i, tbat1, tbat2, tbat3, tbat4, tbrd = battery.telem_summary()

                    #print(f"{chargeWh}, {chargeAh}, {v}, {i}, {recordtime}, {tbat1}, {tbat2}, {tbat3}, {tbat4}, {tbrd}, {cycle}")
                    chargeWh += v * i * (recordtime - lastpolltime) / 3600
                    chargeAh += i * (recordtime - lastpolltime) / 3600
                    log = open(filename, "a")
                    log.write(f"{chargeWh},{chargeAh},{v},{i},{time.perf_counter()},{tbat1},{tbat2},{tbat3},{tbat4},{tbrd},{cycle},hold\n")
                    log.close()
                    eps.commands["Reset Watchdog"]() # Ping EPS to avoid reset
                    time.sleep(.5)
                print(f"End Charge Hold {time.perf_counter()}")
                eps.commands["Pin On"](LOADPDM) # Configure for discharge
                eps.commands["Pin Off"](FETPDM)
                charging = False
        
        if (not charging) and v < EODC:
            print(f"Discharge Finished, configuring for charge and incrementing cycle, capacity {chargeWh} Wh")
            eps.commands["Pin Off"](LOADPDM) # Configure for charge
            eps.commands["Pin On"](FETPDM)
            charging = True
            cycle += 1 # Increment cycle
            print("Success")

except Exception as e:
    print("Test Aborted " + repr(e))
    eps.commands["Pin On"](FETPDM)
    eps.commands["Pin Off"](LOADPDM)
