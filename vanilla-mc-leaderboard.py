#vanilla-mc-leaderboard.py
#Copyright (C) 2020 Alexander Theulings, ketchupcomputing.com <alexander@theulings.com>
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
# 
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
# 
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
#Documentation for this file can be found at https://ketchupcomputing.com/projects/mc-leaderboard/

#Directory Settings
localWorkingDir = "/tmp/";
dirPrefix = "MCDataParse"

#Minecraft server settings
ftpAddr = "1.2.3.4"
ftpUname = "ftp.username"
ftpPword = "ftp.passowrd"
ftpUserDir = "/world/playerdata/"

#Output to MYSQL settings
outputMYSQL = False
mysqlAddr = "localhost"
mysqlUname = "database.username"
mysqlPword = "database.password"
mysqlDB = "database.name"
mysqlTableName = "leaderboard"

#Output to HTML settings
outputHTML = True
siteDir = "/var/www/scores/"
displayPoweredBy = True

import datetime
import nbt
import os
import requests
import time
from ftplib import FTP
import mysql.connector

#Create a directory to work in
fullWorkingDir = localWorkingDir + dirPrefix + str(time.time())
os.mkdir(fullWorkingDir)
os.chdir(fullWorkingDir)

#Connect to Minecraft server
ftp = FTP(ftpAddr)
ftp.login(ftpUname, ftpPword)
ftp.cwd(ftpUserDir)
fileList = ftp.nlst()
scoreMap = {};

#Connect to database if enabled
if outputMYSQL:
    connection = mysql.connector.connect(host=mysqlAddr, database=mysqlDB, user=mysqlUname, password=mysqlPword)
    cursor = connection.cursor(prepared=True)

today = datetime.datetime.now().strftime("%Y-%m-%d")
fullDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#Download player files and extract scores
for listing in fileList:
    with open(listing, 'wb') as fp:
        ftp.retrbinary('RETR ' + listing, fp.write)
    nbtfile = nbt.nbt.NBTFile(listing,'rb')
    scoreMap[listing] = str(nbtfile["Score"])
    #Put the score into the database if it is enabled
    #We do not request the player's username at this point as it should be requested when displayed
    if outputMYSQL:
        cursor.execute("INSERT INTO " + mysqlTableName + " (uuid, score, time) VALUES (%s, %s, %s)",
                            (listing.replace(".dat", ""), int(str(nbtfile["Score"])), fullDate))

if outputMYSQL:
    connection.commit()
    cursor.close()
    connection.close()

#If HTML output is enabled create a list of the top 10 players
if outputHTML:
    sortedScores = sorted(scoreMap.items(), key=lambda x:int(x[1]))
    topScores = ""
    for i in range(len(sortedScores) - 1, len(sortedScores) - 11, -1):
        #Get player's current username
        apiRaw = requests.get("https://api.mojang.com/user/profiles/" + sortedScores[i][0].replace('-', '').replace(".dat", '') + "/names")
        apiJson = apiRaw.json()
        name = apiJson[len(apiJson)-1]["name"]
        topScores += str(len(sortedScores) - i) + ": " + name + " - " + sortedScores[i][1] + "<br>" 

    topScores = "Scores as of " + fullDate + " UTC<br><hr><br>" + topScores
    if displayPoweredBy:
        topScores = topScores + "<br><p style=\"font-size: small\">Powered by <a href=\"https://ketchupcomputing.com/projects/mc-leaderboard\">vanilla-mc-leaderboard</a></p>."

    os.chdir(siteDir)
    f = open("latest.html", "w")
    f.write(topScores)
    f.close()

    f = open(today + ".html", "w")
    f.write(topScores)
    f.close()
