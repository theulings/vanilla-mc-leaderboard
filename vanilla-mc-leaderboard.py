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

#Output to SQL settings
outputSQL = False
cacheSQL = False
cacheFor = 168
sqlAddr = "localhost"
sqlUname = "database.username"
sqlPword = "database.password"
sqlDB = "database.name"
sqlTableName = "leaderboard"

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

def retrUsername(uuid):
    apiRaw = requests.get("https://api.mojang.com/user/profiles/" + uuid.replace('-', '') + "/names")
    apiJson = apiRaw.json()
    name = apiJson[len(apiJson)-1]["name"]
    if cacheSQL:
        cursor.execute("INSERT INTO mcUnameCache (uuid, uname) VALUES (%s, %s)", [uuid, name])
    return name


def getUsername(uuid):
    if cacheSQL:
        cursor.execute("SELECT uname FROM mcUnameCache WHERE uuid=%s", [uuid])
        if cursor.rowcount > 0:
            results = cursor.fetchall()
            return results[0][0]
        else:
            return retrUsername(uuid)

    else:
        return retrUsername(uuid)


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
if outputSQL or cacheSQL:
    connection = mysql.connector.connect(host=sqlAddr, database=sqlDB, user=sqlUname, password=sqlPword)
    cursor = connection.cursor(buffered=True)

#If caching clear out of date records
if cacheSQL:
    cursor.execute("DELETE FROM mcUnameCache WHERE time < (NOW() - INTERVAL " + str(cacheFor) + " HOUR)");

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
    if outputSQL:
        cursor.execute("INSERT INTO " + sqlTableName + " (uuid, score, time) VALUES (%s, %s, %s)",
                            [listing.replace(".dat", ""), int(str(nbtfile["Score"])), fullDate])

#If HTML output is enabled create a list of the top 10 players
if outputHTML:
    sortedScores = sorted(scoreMap.items(), key=lambda x:int(x[1]))
    topScores = ""
    for i in range(len(sortedScores) - 1, len(sortedScores) - 11, -1):
        #Get player's username
        name = getUsername(sortedScores[i][0].replace(".dat", ''))
        topScores += str(len(sortedScores) - i) + ": " + name + " - " + sortedScores[i][1] + "<br>" 

    topScores = "Scores as of " + fullDate + " UTC<br><hr><br>" + topScores
    if displayPoweredBy:
        topScores = topScores + "<br><p style=\"font-size: small\">Powered by <a href=\"https://ketchupcomputing.com/projects/mc-leaderboard\" target=\"_blank\">vanilla-mc-leaderboard</a>.</p>"

    os.chdir(siteDir)
    f = open("latest.html", "w")
    f.write(topScores)
    f.close()

    f = open(today + ".html", "w")
    f.write(topScores)
    f.close()

if outputSQL or cacheSQL:
    connection.commit()
    cursor.close()
    connection.close()
