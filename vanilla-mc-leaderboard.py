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
sqlAddr = "localhost"
sqlUname = "database.username"
sqlPword = "database.password"
sqlDB = "database.name"
sqlTableName = "leaderboard"

import datetime
import nbt
import os
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
connection = mysql.connector.connect(host=sqlAddr, database=sqlDB, user=sqlUname, password=sqlPword)
cursor = connection.cursor(buffered=True)

today = datetime.datetime.now().strftime("%Y-%m-%d")
fullDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#Download player files and extract scores
for listing in fileList:
    if listing.endswith(".dat_old"):
        continue
    with open(listing, 'wb') as fp:
        ftp.retrbinary('RETR ' + listing, fp.write)
    nbtfile = nbt.nbt.NBTFile(listing,'rb')
    scoreMap[listing] = str(nbtfile["Score"])
    cursor.execute("INSERT INTO " + sqlTableName + " (uuid, score, time) VALUES (%s, %s, %s)",
                            [listing.replace(".dat", ""), int(str(nbtfile["Score"])), fullDate])

connection.commit()
cursor.close()
connection.close()
