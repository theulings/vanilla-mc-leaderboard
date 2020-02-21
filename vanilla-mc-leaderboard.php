<?php
//vanilla-mc-leaderboard.php
//Copyright (C) 2020 Alexander Theulings, ketchupcomputing.com <alexander@theulings.com>
//
//This program is free software: you can redistribute it and/or modify
//it under the terms of the GNU General Public License as published by
//the Free Software Foundation, either version 3 of the License, or
//(at your option) any later version.
// 
//This program is distributed in the hope that it will be useful,
//but WITHOUT ANY WARRANTY; without even the implied warranty of
//MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//GNU General Public License for more details.
// 
//You should have received a copy of the GNU General Public License
//along with this program.  If not, see <http://www.gnu.org/licenses/>.
// 
//Documentation for this file can be found at https://ketchupcomputing.com/projects/mc-leaderboard/
//
//This script displays scores parsed by vanilla-mc-leaderboard.py

class vanillaMcLeaderboard{
    //Settings
    private const mysqlAddr = "localhost";
    private const mysqlUname = "database.username";
    private const mysqlPword = "database.password";
    private const mysqlDB = "database.name";
    private const cacheFor = 168;
    private const displayPoweredBy = true;

    //Displays the top 10 scores on the leaderboard at time of provided timestamp
    //If no timestamp has been provided (0) the latest scores will be used
    public static function display($timestamp = 0){
        //Connect to db
        $dbConn = new mysqli(self::mysqlAddr, self::mysqlUname, self::mysqlPword, self::mysqlDB);
        if ($dbConn->connect_error){
            die("Connection to database failed - " . $dbConn->connect_error);
        }

        //If no timestamp has been requested get the last inserted timestamp from the database
        if($timestamp == 0){
            $timeResult = $dbConn->query("select `time` from `leaderboard` ORDER BY `id` DESC LIMIT 1");
            $timestamp = $timeResult->fetch_assoc()["time"];
            $timeResult->free();
        }
        
        //Delete out of date username caches
        $stmt = $dbConn->prepare("DELETE FROM `mcUnameCache` WHERE `time` < (NOW() - INTERVAL ? HOUR)");
        $cacheLen = self::cacheFor;
        $stmt->bind_param("i", $cacheLen);
        $stmt->execute();
        $stmt->close();

        //Get leaderboard
        $stmt = $dbConn->prepare("SELECT `uuid`, `score` FROM `leaderboard` WHERE `time`=? ORDER BY `score` DESC LIMIT 10");
        $stmt->bind_param("s", $timestamp);
        $stmt->execute();
        $results = $stmt->get_result();

        //Display leaderboard
        echo "Scores as of " . $timestamp . " UTC<br><hr><br>";
        $pos = 1;
        while($row = $results->fetch_assoc()){
            echo $pos . ": " . self::getUsername($row["uuid"]) . " - " . $row["score"] . "<BR>";
            $pos ++;
        }
        $stmt->close();
        $dbConn->close();

        if (self::displayPoweredBy){
            echo "<br><p style=\"font-size: small\">Powered by <a href=\"https://ketchupcomputing.com/projects/mc-leaderboard\" target=\"_blank\">vanilla-mc-leaderboard</a>.</p>";
        }
    }

    //Get name from database if cached
    private static function getUsername($uuid){
        //Connect to db
        $dbConn = new mysqli(self::mysqlAddr, self::mysqlUname, self::mysqlPword, self::mysqlDB);
        if ($dbConn->connect_error){
            die("Connection to database failed - " . $dbConn->connect_error);
        }

        $stmt = $dbConn->prepare("SELECT `uname` FROM `mcUnameCache` WHERE `uuid`=?");
        $stmt->bind_param("s", $uuid);
        $stmt->execute();
        $results = $stmt->get_result();
        if($results->num_rows == 0){
            //Not cached, get it from Mojang
            $stmt->close();
            $dbConn->close();
            return self::retrieveUsername($uuid);
        }else{
            $row = $results->fetch_assoc();
            $uname = $row["uname"];
            $stmt->close();
            $dbConn->close();
            return $uname;
        }
    }

    //Gets username from Mojang and caches it
    private static function retrieveUsername($uuid){
        //Connect to db
        $dbConn = new mysqli(self::mysqlAddr, self::mysqlUname, self::mysqlPword, self::mysqlDB);
        if ($dbConn->connect_error){
            die("Connection to database failed - " . $dbConn->connect_error);
        }
       
        //Remove old records of uuid
        $stmt = $dbConn->prepare("DELETE FROM `mcUnameCache` WHERE `uuid`=?");
        $stmt->bind_param("s", $uuid);
        $stmt->execute();
        $stmt->close();

        //Get username from Mojang
        $cutUuid = str_replace ("-", "", $uuid);
        $unameData = file_get_contents("https://api.mojang.com/user/profiles/" . $cutUuid . "/names");
        $unameJson = json_decode($unameData);
        $uname = $unameJson[count($unameJson) - 1]->{"name"};
        
        //Store username in database
        $stmt = $dbConn->prepare("INSERT INTO `mcUnameCache` (uuid, uname) VALUES (?, ?)");
        $stmt->bind_param("ss", $uuid, $uname);
        $stmt->execute();
        $stmt->close();
        $dbConn->close();
        return $uname;
    }
}
