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
    private static $sqlAddr = "localhost";
    private static $sqlUname = "database.username";
    private static $sqlPword = "database.password";
    private static $sqlDB = "database.name";
    private static $sqlMainTableName = "database.table.name";

    private static $mcUnamesTable = "database.table.name";
    private static $mcUnamesCacheFor = 168;

    private static $htmlPre = "Records as of %t UTC<br><hr><br>";
    private static $htmlRow = "%p: %u - %c<BR>";
    private static $htmlPost = "";

    private static $displayPoweredBy = true;

    public static function display($displayStoreId = 0, $resultCount = 25, $timestamp = 0, $useExternalConfig = null){
        //Load config from file
        if ($useExternalConfig != null){
            $configFile = fopen($useExternalConfig, "r");
            $configJson = fread($configFile, filesize($useExternalConfig));
            fclose($configFile);
            $config = json_decode($configJson, true);

            self::$sqlAddr = $config["sql"]["address"];
            self::$sqlUname = $config["sql"]["username"];
            self::$sqlPword = $config["sql"]["password"];
            self::$sqlDB = $config["sql"]["name"];
            self::$sqlMainTableName = $config["sql"]["main_table_name"];

            self::$mcUnamesTable = $config["username_records"]["sql_table_name"];

            self::$htmlPre = $config["html_output"]["pre"];
            self::$htmlRow = $config["html_output"]["row"];
            self::$htmlPost = $config["html_output"]["post"];
            self::$displayPoweredBy = $config["html_output"]["display_powered_by"];
        }

        //Connect to db
        $dbConn = new mysqli(self::$sqlAddr, self::$sqlUname, self::$sqlPword, self::$sqlDB);
        if ($dbConn->connect_error){
            echo "vanilla-mc-leaderboard encountered an error. See site log for more details.";
            error_log("vanilla-mc-leaderboard error connecting to database: " . $dbConn->connect_error);
            return false;
        }

        //If no timestamp has been requested get the last inserted timestamp from the database
        if($timestamp == 0){
            $stmt = $dbConn->prepare("SELECT `time` FROM " . self::$sqlMainTableName . " WHERE `store_id`=? ORDER BY `id` DESC LIMIT 1");
            $stmt->bind_param("i", $displayStoreId);
            $stmt->execute();
            $timestamp = $stmt->get_result()->fetch_assoc()["time"];
            $stmt->close();
        }
        
        //Get leaderboard
        $stmt = $dbConn->prepare("SELECT `uuid`, count FROM " . self::$sqlMainTableName . " WHERE `time`=? AND `store_id`=? ORDER BY `count` DESC LIMIT ?");
        $stmt->bind_param("sii", $timestamp, $displayStoreId, $resultCount);
        $stmt->execute();
        $results = $stmt->get_result();

        //Display leaderboard
        echo str_replace("%t", $timestamp, self::$htmlPre);
        $pos = 1;
        while($row = $results->fetch_assoc()){
            $rowStr = str_replace("%p", $pos, self::$htmlRow);
            $rowStr = str_replace("%u", self::getUsername($row["uuid"]), $rowStr);
            $rowStr = str_replace("%c", $row["count"], $rowStr);
            echo $rowStr;
            $pos ++;
        }
        $stmt->close();
        $dbConn->close();
        echo self::$htmlPost;

        if (self::$displayPoweredBy){
            echo "<br><p style=\"font-size: small\">Powered by <a href=\"https://ketchupcomputing.com/docs/mc-leaderboard\" target=\"_blank\">vanilla-mc-leaderboard</a>.</p>";
        }
    }

    //Get name from database if cached
    private static function getUsername($uuid){
        //Connect to db
        $dbConn = new mysqli(self::$sqlAddr, self::$sqlUname, self::$sqlPword, self::$sqlDB);
        if ($dbConn->connect_error){
            die("Connection to database failed - " . $dbConn->connect_error);
        }

        $stmt = $dbConn->prepare("SELECT `uname` FROM " . self::$mcUnamesTable . " WHERE `uuid`=? LIMIT 1");
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
        $dbConn = new mysqli(self::$sqlAddr, self::$sqlUname, self::$sqlPword, self::$sqlDB);
        if ($dbConn->connect_error){
            die("Connection to database failed - " . $dbConn->connect_error);
        }
       
        //Remove old records of uuid
        $stmt = $dbConn->prepare("DELETE FROM " . self::$mcUnamesTable . " WHERE `uuid`=?");
        $stmt->bind_param("s", $uuid);
        $stmt->execute();
        $stmt->close();

        //Get username from Mojang
        $cutUuid = str_replace ("-", "", $uuid);
        $unameData = file_get_contents("https://api.mojang.com/user/profiles/" . $cutUuid . "/names");
        $unameJson = json_decode($unameData);
        $uname = $unameJson[count($unameJson) - 1]->{"name"};
        
        //Store username in database
        $stmt = $dbConn->prepare("INSERT INTO " . self::$mcUnamesTable . " (uuid, uname) VALUES (?, ?)");
        $stmt->bind_param("ss", $uuid, $uname);
        $stmt->execute();
        $stmt->close();
        $dbConn->close();
        return $uname;
    }
}
