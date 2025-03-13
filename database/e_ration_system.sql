CREATE DATABASE  e_ration_system3;
USE e_ration_system3;

CREATE TABLE users (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(100) NOT NULL,
  email varchar(100) NOT NULL,
  password varchar(255) NOT NULL,
  phone varchar(15) NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE ration_items (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) NOT NULL,
  description text NOT NULL,
  stock int(11) NOT NULL,
  unit varchar(10) NOT NULL,
  image varchar(255) NOT NULL,
  rate decimal(10,2) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE user_item_stock (
  id int(11) NOT NULL AUTO_INCREMENT,
  user_id int(11) NOT NULL,
  item_id int(11) NOT NULL,
  allocated_stock int(11) NOT NULL,
  available_stock int(11) NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  FOREIGN KEY (item_id) REFERENCES ration_items (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE family_members (
  member_id int(11) NOT NULL AUTO_INCREMENT,
  user_id int(11) NOT NULL,
  name varchar(100) NOT NULL,
  age int(11) NOT NULL,
  gender enum('Male','Female','Other') NOT NULL,
  relation varchar(50) NOT NULL,
  PRIMARY KEY (member_id),
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;