# Library Management System

## Installation

1. Ensure you have Python 3.6 or higher installed on your system.
2. Install the required dependencies by running the following command in your terminal:
   ```
   pip install -r requirements.txt
   ```
3. Create a MySQL database and update the database connection details in the `db.py` file.

## Usage

1. Run the `main.py` file to start the application.
2. The application will prompt you to create a new account or log in.
3. After logging in, you can access various features of the library management system, such as:
   - Apply for a library card
   - View book details
   - View borrower details
   - Add new books
   - Issue books
   - Return books
   - Manage users (for admin users)
   - Manage books (for admin users)
   - Manage linked devices

## Local Imports

The application uses the following Local imports:

1. `db.py`: Provides database connection and CRUD operations for the library management system.
2. `Email_sender.py`: Handles the sending of email notifications to borrowers with overdue books.
3. `link_device.py`: Manages the connection between the desktop application and the mobile scanner app.

## Contributing

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and ensure all tests pass.
4. Submit a pull request with a detailed description of your changes.
