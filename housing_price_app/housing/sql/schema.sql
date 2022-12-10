DROP TABLE IF EXISTS city;
DROP TABLE IF EXISTS city_layout;
DROP TABLE IF EXISTS city_housing;

CREATE TABLE city (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  city_name TEXT NOT NULL,
  city_lat REAL NOT NULL,
  city_lng REAL NOT NULL
);


CREATE TABLE city_layout (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  landmark_name TEXT NOT NULL,
  landmark_type TEXT NOT NULL,
  landmark_lat REAL NOT NULL,
  landmark_lng REAL NOT NULL,
  landmark_rating REAL NOT NULL,
  city_id INTEGER,
  FOREIGN KEY (city_id) REFERENCES city (id)
);


CREATE TABLE city_housing (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crawled_date TEXT,
  house_address TEXT,
  price REAL,
  area REAL,
  num_bathroom REAL,
  num_bedroom REAL,
  num_days_posted REAL,
  zillow_url TEXT,
  house_lat REAL,
  house_lng REAL,
  city_id INTEGER,
  FOREIGN KEY (city_id) REFERENCES city (id)
);



