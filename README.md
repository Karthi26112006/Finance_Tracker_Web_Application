## Personal Finance Tracker (Web Application)
This project is a full-stack web application designed to help users manage their finances by tracking income and expenses through a secure, organized interface. It utilizes a dynamic database structure to isolate user data and organize records by month.

## Key Features
Secure Authentication: Implements a robust user system with registration and login, utilizing Werkzeug for password hashing and session management.

Dynamic SQL Table Management: Automatically generates unique MySQL tables for each user and specific month (e.g., Finance_Tracker_1_03_2026), ensuring data isolation and performance.

Complete CRUD Operations: Users can Create, Read, Update, and Delete transactions, with each entry tracking the date, category, description, and amount.

Automated Financial Summary: Features an API-driven summary that calculates total income, total expenses, and the current balance in real-time.

Input Validation & Security: Includes checks for table ownership to prevent unauthorized access to data between different users.

## Technical Stack
Backend: Python with the Flask framework.

Database: MySQL for relational data storage and structured querying.

Authentication: Werkzeug Security.

Database Connector: mysql-connector-python for executing SQL commands directly from Python.

## Project Architecture
The application follows a RESTful design where the Flask backend serves as an API layer. When a user logs in, the system verifies their credentials and then creates or loads a specific table for the chosen month. This approach demonstrates advanced SQL handling by managing multiple tables dynamically rather than using a single bloated table.

## Floder Name Add Files

Name : templates

Add Files : 1 - index.html ,2 - login.html ,3 - register.html


Name : static

Add Files : 1 - script.js ,2 - style.css
