## Reads exisiting simulation png images and adds a graph showing prescribed head kinematics up to the time of each frame
## Run with python3 input.json 
import matplotlib.pyplot as plt
import numpy as np
import xml.etree.ElementTree as ET
import sys
import os
import json
import glob

nRes = 100

jsonFile = sys.argv[1]
inputJson = json.loads(open(jsonFile).read())
uid = inputJson["uid"]
simulationJson = inputJson["simulation"]
meshFile = simulationJson["mesh"]
mesh = os.path.splitext(meshFile)[0]

# Read time steps reported in pvd files
pvdFile = glob.glob("*.pvd")[0]
print(f"Loading ParaView file: {pvdFile}")

tree = ET.parse(pvdFile)
root = tree.getroot()

count = 0
key1 = 'timestep'
for elem in root.iter():
    if (elem.tag=="DataSet"):
        count = count + 1
tArrayRaw = np.zeros(count)
count1 = 0

for elem in root.iter():
    if (elem.tag=="DataSet"):
        tArrayRaw[count1] = float(elem.attrib[key1])
        count1 = count1 + 1
# Convert tArray to millisec
tArrayRaw = tArrayRaw*1000

countFull = (count-1)*nRes+1
tArray = np.zeros(countFull)

for tA in np.arange(count-1):
    localT = np.linspace(tArrayRaw[tA], tArrayRaw[tA+1], nRes+1)
    tArray[tA*nRes:(tA+1)*nRes] = localT[:-1]
tArray[-1] = tArrayRaw[-1]

if type(simulationJson["linear-acceleration"]) == dict:
    linXt = simulationJson["linear-acceleration"]["xt"]
    linXv = simulationJson["linear-acceleration"]["xv"]
    linYt = simulationJson["linear-acceleration"]["yt"]
    linYv = simulationJson["linear-acceleration"]["yv"]
    linZt = simulationJson["linear-acceleration"]["zt"]
    linZv = simulationJson["linear-acceleration"]["zv"]
    angXt = simulationJson["angular-acceleration"]["xt"]
    angXv = simulationJson["angular-acceleration"]["xv"]
    angYt = simulationJson["angular-acceleration"]["yt"]
    angYv = simulationJson["angular-acceleration"]["yv"]
    angZt = simulationJson["angular-acceleration"]["zt"]
    angZv = simulationJson["angular-acceleration"]["zv"]

    linArrayX = np.interp(tArray, linXt, linXv)
    linArrayY = np.interp(tArray, linYt, linYv)
    linArrayZ = np.interp(tArray, linZt, linZv)
    linArray = np.sqrt(linArrayX**2+linArrayY**2+linArrayZ**2)/9.81 # Convert to g's
    angArrayX = np.interp(tArray, angXt, angXv)
    angArrayY = np.interp(tArray, angYt, angYv)
    angArrayZ = np.interp(tArray, angZt, angZv)
    angArray = np.sqrt(angArrayX**2+angArrayY**2+angArrayZ**2)

else: # Linear acceleration assumed to be a list
    linT = np.zeros(3); linV = np.zeros(3)
    angT = np.zeros(3); angV = np.zeros(3)
    tPeak = simulationJson["time-peak-acceleration"]
    tMax = simulationJson["maximum-time"]
    linAccMax = simulationJson["linear-acceleration"]
    angAccMax = simulationJson["angular-acceleration"]
    linT[1] = angT[1] = tPeak
    linT[2] = angT[2] = tMax
    linV[1] = np.sqrt(linAccMax[0]**2+linAccMax[1]**2+linAccMax[2]**2)
    if type(angAccMax) == list:
        angV[1] = np.sqrt(angAccMax[0]**2+angAccMax[1]**2+angAccMax[2]**2)
    else: # Size 1
        angV[1] = angAccMax
    linArray = np.interp(tArray, linT, linV)
    angArray = np.interp(tArray, angT, angV)

tMax = tArray[-1]
linMax = (int(np.max(linArray)/10)+2)*10
angMax = (int(np.max(angArray)/100)+2)*100

for fileCount in range(count1):
    img = plt.imread("injury_"+uid+".%04d.png"%fileCount)

    figure = plt.figure(figsize=(11,8))
    plt.imshow(img)
    plt.axis('off')
    color1 = plt.cm.viridis(0.90)
    color2 = plt.cm.viridis(0.50)

    tt = tArray[:fileCount*nRes+1]
    axes2 = figure.add_axes([0.18, 0.58, 0.2, 0.18]) # inset axes

    p1 = axes2.twinx()

    l1, = axes2.plot(tt, linArray[:fileCount*nRes+1], color=color1, label="Linear")
    axes2.set_xlim(0, tMax);
    axes2.set_ylim(0, linMax);

    p1.set_ylim(0, angMax);
    l2, = p1.plot(tt, angArray[:fileCount*nRes+1], color=color2, linestyle='--', label="Angular")

    axes2.set_facecolor((.80, .80, .80))
    label = axes2.set_xlabel("time [ms]", color="white")
    label = axes2.set_ylabel("acceleration [g]", color=color1)
    label = p1.set_ylabel(r"[$rad/s^2$]", color=color2)
    axes2.tick_params(labelcolor='white')
    p1.tick_params(labelcolor='white')
    lns = [l1, l2]
    axes2.legend(handles=lns, loc='upper right', fontsize=7)
    axes2.grid(False)
    p1.grid(False)

    plt.savefig("updated_injury_"+uid+".%04d.png"%fileCount,
            bbox_inches='tight', dpi = 252)
    plt.close()
