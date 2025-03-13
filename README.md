# E-Ration System

## Overview
The E-Ration System is a digital platform designed to manage the distribution of ration supplies efficiently. It automates stock allocation based on family size and provides a structured approach to ration distribution.

## Features
- User Registration with Family Details
- Automatic Stock Allocation
- Admin Dashboard for Monitoring and Management
- Database-Driven System Using MySQL
- Web Interface Built with Flask

## Project Structure
```
Project/
│── app.py                     # Main Flask application
│── database/
│   ├── e_ration_system.sql     # Database schema
│── static/
│   ├── images/                 # Contains UI images
│── templates/                  # HTML templates for web pages
│── .idea/                      # IDE configuration files
```

## Installation

### Prerequisites
- Python 3.x
- MySQL Database
- Required Python Libraries (`Flask`, `MySQL-connector`, `APScheduler`)

### Setup
1. Clone or extract the project.
2. Install required dependencies:
   ```bash
   pip install flask mysql-connector-python apscheduler
   ```
3. Set up the MySQL database:
   - Import `e_ration_system.sql` into MySQL.
   - Update database credentials in `app.py` if needed.

4. Run the application:
   ```bash
   python app.py
   ```
5. Open the browser and navigate to `http://127.0.0.1:5000`.

## Future Enhancements
- Adding AI-based demand prediction
- Integrating government APIs for real-time ration tracking
- Mobile application support

## License
This project is for educational purposes.

## Contact
For any queries, feel free to reach out.

