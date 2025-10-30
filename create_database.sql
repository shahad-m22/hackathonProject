-- Create the database
CREATE DATABASE IF NOT EXISTS nibbah_factory;
USE nibbah_factory;

-- Create users table
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- Create machines table WITHOUT risk_level (we calculate it dynamically)
CREATE TABLE machines (
    machine_id INT AUTO_INCREMENT PRIMARY KEY,
    machine_name VARCHAR(100) NOT NULL,
    criticality INT NOT NULL CHECK (criticality BETWEEN 1 AND 10),
    hourly_downtime_cost DECIMAL(12,2),
    total_maintenance_cost DECIMAL(12,2),
    last_maintenance DATE,
    next_maintenance DATE,
    life_time_years INT
);

-- Insert your user data
INSERT INTO users (user_id, password_hash, email) VALUES 
(11011, '11011-Qq', 'A11011@gmail.com'),
(11022, '11022-Qq', 'B11022@gmail.com'),
(11033, '11033-Qq', 'C11033@gmail.com'),
(11044, '11044-Qq', 'D11044@gmail.com'),
(11055, '11055-Qq', 'E11055@gmail.com');