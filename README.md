# Hosting and support available at [ketchupcomputing.com/projects/mc-leaderboard](https://ketchupcomputing.com/projects/mc-leaderboard)

## Pip3 packages required
mysql-connector, nbt

## Database schemas
    CREATE TABLE leaderboard (
	    id INT(11) auto_increment,
	    uuid VARCHAR(36),
	    score INT(10),
	    time DATETIME,
	    PRIMARY KEY (id)
    );

    CREATE TABLE mcUnameCache (
        id INT(11) auto_increment,
        uuid VARCHAR(36),
        uname VARCHAR(16),
        time DATETIME DEFAULT current_timestamp(),
        PRIMARY KEY (id)
    );

## Using the PHP script

    include "vanilla-mc-leaderboard/vanilla-mc-leaderboard.php";
    vanillaMcLeaderboard::display();

## Legal Information
Copyright (C) 2020 Alexander Theulings, ketchupcomputing.com <[alexander@theulings.com](mailto:alexander@theulings.com)>

Distributed under the GNU General Public License version 3 or later, see LICENCE.

