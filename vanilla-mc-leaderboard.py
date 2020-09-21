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
#

import datetime
import nbt
import os
import shutil
import json
import time
from ftplib import FTP
import mysql.connector

class itemPair:
    def __init__(self, setMcItemName, setValue):
        self.mcItemName = setMcItemName
        self.value = setValue

class itemSet:
    def __init__(self, setStoreId, setMinimumCount, setCheckInvent, setCheckEnders, setCheckShulkers, setPairs):
        self.storeId = setStoreId
        self.minimumCount = setMinimumCount
        self.checkInvent = setCheckInvent
        self.checkEnders = setCheckEnders
        self.checkShulkers = setCheckShulkers
        self.pairs = setPairs

def scanStorageFor(storage, forItemName,  checkShulkers):
    count = 0
    for slot in storage:
        if str(slot["id"]) == forItemName:
            count += int(str(slot["Count"]))
        if checkShulkers and str(slot["id"]) == "minecraft:shulker_box":
            if "tag" in slot:
                count += scanStorageFor(slot["tag"]["BlockEntityTag"]["Items"], forItemName, checkShulkers)
    return count

with open('vanilla-mc-leaderboard-config.json') as json_file:
    data = json.load(json_file)

    #Minecraft server settings
    ftpAddr = data['ftp']["address"]
    ftpUname = data['ftp']["username"]
    ftpPword = data['ftp']["password"]
    ftpUserDir = data['ftp']["user_directory"]
    #Output to SQL settings
    sqlAddr = data["sql"]["address"]
    sqlUname = data["sql"]["username"]
    sqlPword = data["sql"]["password"]
    sqlDB = data["sql"]["name"]
    sqlMainTableName = data["sql"]["main_table_name"]
    #Directory Settings
    localWorkingDir = data["working_directory"]["path"]
    dirPrefix = data["working_directory"]["prefix"]
    #Score record settings
    keepScoreRecords = data["score_records"]["keep_score_records"]
    scoreRecordId = data["score_records"]["store_id"]
    minimumScoreThreshold = data["score_records"]["minimum_score"]

    itemRecordSqlTable = data["item_record_sql_table_name"]
    itemSets = []
    for record in data["item_record_sets"]:
        itemPairs = []
        for pair in record["item_pairs"]:
            itemPairs.append(itemPair(pair["name"], pair["value"]))
        itemSets.append(itemSet(record["store_id"], record["minimum_count"], record["check_inventory"], record["check_ender_chest"], record["check_shulkers"], itemPairs))

#Create a directory to work in
fullWorkingDir = localWorkingDir + dirPrefix + str(time.time())
os.mkdir(fullWorkingDir)
os.chdir(fullWorkingDir)

#Connect to Minecraft server
ftp = FTP(ftpAddr)
ftp.login(ftpUname, ftpPword)
ftp.cwd(ftpUserDir)
fileList = ftp.nlst()

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
    if keepScoreRecords:
        if int(str(nbtfile["Score"])) >= minimumScoreThreshold:
            cursor.execute("INSERT INTO " + sqlMainTableName + " (script_id, uuid, count, time) VALUES (%s, %s, %s, %s)", [scoreRecordId, listing.replace(".dat", ""), int(str(nbtfile["Score"])), fullDate])

    for itemSet in itemSets:
        itemCount = 0
        for itemPair in itemSet.pairs:
            if itemSet.checkInvent:
                itemCount += scanStorageFor(nbtfile["Inventory"], itemPair.mcItemName, itemSet.checkShulkers) * itemPair.value
            if itemSet.checkEnders:
                itemCount += scanStorageFor(nbtfile["EnderItems"], itemPair.mcItemName, itemSet.checkShulkers) * itemPair.value

        if itemCount >= itemSet.minimumCount:
            cursor.execute("INSERT INTO " + sqlMainTableName + " (script_id, uuid, count, time) VALUES (%s, %s, %s, %s)", [itemSet.storeId, listing.replace(".dat", ""), itemCount, fullDate])

connection.commit()
cursor.close()
connection.close()

#Delete working directory
os.chdir("..")
shutil.rmtree(fullWorkingDir)
