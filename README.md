# Hosting and support available at [ketchupcomputing.com/projects/mc-leaderboard](https://ketchupcomputing.com/projects/mc-leaderboard)

## Pip3 packages required
mysql-connector, nbt

## Database schema
    `CREATE TABLE leaderboard (`
	    `id INT(11) auto_increment,`
	    `uuid VARCHAR(36),`
	    `score INT(10),`
	    `time DATETIME,`
	    `PRIMARY KEY (id)`
    `);`

## Legal Information
Copyright (C) 2020 Alexander Theulings, ketchupcomputing.com <[alexander@theulings.com](mailto:alexander@theulings.com)>

Distributed under the GNU General Public License version 3 or later, see LICENCE.

