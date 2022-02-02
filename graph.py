import csv
import matplotlib.pyplot as plt

timestamps = []
chargeWh = []
chargeAh = []
volt = []
current = []

with open( 'CycleLog.csv' , newline='' ) as csvfile :
    myreader = csv.reader( csvfile , delimiter=',' , quotechar='"' )
    # header
    for row in myreader :
        # print( row )
        break
    # data
    for row in myreader :
        chargeWh.append(float(row[0]))
        chargeAh.append(float(row[1]))
        volt.append(float(row[2]))
        current.append(float(row[3]))
        timestamps.append(float(row[4]))

offset = timestamps[0]
timestamps = [timestamps[i] - offset for i in range(len(timestamps))]

fig, ax1 = plt.subplots()

color = 'tab:blue'
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Voltage (V)', color=color)
ax1.plot(timestamps, volt, color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()

color = 'tab:orange'
ax2.set_ylabel('Current (A)', color=color)
ax2.plot(timestamps, current, color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()

plt.plot(timestamps, volt, label = "Voltage (V)")
plt.plot(timestamps, current, label = "Current (A)")
