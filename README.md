# Help Desk System

This is a simple help desk system built with Flask and SQLAlchemy. The application allows users to open tickets for various issues without requiring a password. The system intelligently distributes tasks among three technicians based on their technical profiles: networks and infrastructure, IT support, and maintenance. An admin user is included to manage the entire system.

## Features

- User-friendly interface for submitting tickets
- Ticket management for users and technicians
- Admin dashboard for managing technicians and viewing ticket statistics
- Automatic distribution of tickets to technicians based on their profiles

## Project Structure

```
helpdesk-system
├── app
│   ├── __init__.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── ticket.py
│   │   ├── technician.py
│   │   └── user.py
│   ├── routes
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   └── tickets.py
│   ├── templates
│   │   ├── base.html
│   │   ├── admin
│   │   │   ├── dashboard.html
│   │   │   └── manage_technicians.html
│   │   ├── auth
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── tickets
│   │       ├── create.html
│   │       ├── list.html
│   │       └── view.html
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   └── js
│   │       └── main.js
│   └── utils
│       ├── __init__.py
│       └── ticket_distributor.py
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd helpdesk-system
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database (if applicable):
   ```
   # Add database setup instructions here
   ```

## Usage

To run the application, execute the following command:
```
python run.py
```

Visit `http://127.0.0.1:5000` in your web browser to access the help desk system.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.