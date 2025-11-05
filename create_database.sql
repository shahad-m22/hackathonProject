-- Create the database
CREATE DATABASE IF NOT EXISTS nabeh_factory;
USE nabeh_factory;

-- Create users table
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- Create machines table
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

-- Create machine state tracking table
CREATE TABLE machine_states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id INT,
    risk_state ENUM('Low', 'Medium', 'High'),
    last_notification_sent DATE,
    notification_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
);

-- Add notification logs table
CREATE TABLE IF NOT EXISTS notification_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipient VARCHAR(255),
    subject TEXT,
    machine_name VARCHAR(100),
    alert_type VARCHAR(50),
    status VARCHAR(50),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert user data
INSERT INTO users (user_id, password_hash, email) VALUES
(11011, '11011-Qq', 'technician1@nabehfactory.com'),
(11022, '11022-Qq', 'technician2@nabehfactory.com'),
(11033, '11033-Qq', 'manager@nabehfactory.com'),
(11044, '11044-Qq', 'maintenance@nabehfactory.com'),
(11055, '11055-Qq', 'operations@nabehfactory.com');

-- Create index for better performance
CREATE INDEX idx_machine_states ON machine_states(machine_id, risk_state);