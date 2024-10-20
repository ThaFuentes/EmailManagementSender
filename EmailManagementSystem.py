# Import statements
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox,
    QCheckBox, QTextEdit, QListWidget, QDialog, QComboBox, QHBoxLayout, QFrame,
    QInputDialog, QToolButton, QMenu, QListWidgetItem, QLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QRect, QSize, QPoint
from PyQt5.QtGui import QIcon  # Import QIcon for window icons
import sys
import smtplib
import sqlite3
from cryptography.fernet import Fernet
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import ssl
import json  # Import json module
from functools import partial  # Import partial for button callbacks

# Encryption key generation and storage
key_file_path = "secret.key"
if os.path.exists(key_file_path):
    with open(key_file_path, "rb") as key_file:
        key = key_file.read()
else:
    key = Fernet.generate_key()
    with open(key_file_path, "wb") as key_file:
        key_file.write(key)
cipher_suite = Fernet(key)

# SQLite setup for storing user data
db_file = "lead_data.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS EmailConfig (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    smtp_server TEXT NOT NULL,
    smtp_port INTEGER NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    use_tls INTEGER NOT NULL,
    use_ssl INTEGER NOT NULL
)
''')
conn.commit()


class MainProgram(QWidget):
    def __init__(self):
        super().__init__()

        # Set window icon
        self.setWindowIcon(QIcon('icon.png'))

        # Check if a user exists in the database
        cursor.execute("SELECT * FROM Users")
        user_exists = cursor.fetchone() is not None

        # Set up the window properties
        self.setWindowTitle("Email Management System")
        self.setGeometry(100, 100, 600, 350)

        # Create layout and widgets
        layout = QVBoxLayout()

        if not user_exists:
            # Create User Section
            self.create_user_label = QLabel("Create an Admin Account:", self)
            layout.addWidget(self.create_user_label)

            self.new_username_field = QLineEdit(self)
            self.new_username_field.setPlaceholderText("New Username")
            layout.addWidget(self.new_username_field)

            self.new_password_field = QLineEdit(self)
            self.new_password_field.setPlaceholderText("New Password")
            self.new_password_field.setEchoMode(QLineEdit.Password)
            layout.addWidget(self.new_password_field)

            self.create_user_button = QPushButton("Create Account", self)
            self.create_user_button.clicked.connect(self.create_user)
            layout.addWidget(self.create_user_button)
        else:
            # Login Section
            self.login_label = QLabel("Enter your login credentials:", self)
            layout.addWidget(self.login_label)

            self.username_field = QLineEdit(self)
            self.username_field.setPlaceholderText("Username")
            layout.addWidget(self.username_field)

            self.password_field = QLineEdit(self)
            self.password_field.setPlaceholderText("Password")
            self.password_field.setEchoMode(QLineEdit.Password)
            layout.addWidget(self.password_field)

            self.remember_user_checkbox = QCheckBox("Remember me", self)
            layout.addWidget(self.remember_user_checkbox)

            # Load remembered username if it exists
            if os.path.exists("remember_user.txt"):
                with open("remember_user.txt", "r") as file:
                    remembered_username = file.read().strip()
                    self.username_field.setText(remembered_username)
                    self.remember_user_checkbox.setChecked(True)

            self.login_button = QPushButton("Login", self)
            self.login_button.clicked.connect(self.login)
            layout.addWidget(self.login_button)

            # Enable pressing 'Enter' to login
            self.username_field.returnPressed.connect(self.login)
            self.password_field.returnPressed.connect(self.login)

        # Set layout
        self.setLayout(layout)

    def create_user(self):
        username = self.new_username_field.text()
        password = self.new_password_field.text()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter a valid username and password.")
            return

        # Store the new user in the database
        cursor.execute('''
            INSERT INTO Users (username, password) VALUES (?, ?)
        ''', (username, password))
        conn.commit()

        QMessageBox.information(self, "Account Created", "Admin account created successfully!")
        self.reload_login()

    def reload_login(self):
        # Reload the login screen after creating a user
        self.close()
        self.__init__()
        self.show()

    def login(self):
        username = self.username_field.text()
        password = self.password_field.text()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter your username and password.")
            return

        # Check credentials in the database
        cursor.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
        if cursor.fetchone():
            if self.remember_user_checkbox.isChecked():
                # Store the username to remember the user
                with open("remember_user.txt", "w") as file:
                    file.write(username)
            elif os.path.exists("remember_user.txt"):
                # Remove the remembered username if checkbox is unchecked
                os.remove("remember_user.txt")
            QMessageBox.information(self, "Login Successful", "Welcome!")
            self.open_main_interface()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def open_main_interface(self):
        # Create the main interface window
        self.main_window = MainInterface()
        self.main_window.show()
        self.close()


class MainInterface(QWidget):
    def __init__(self):
        super().__init__()

        # Set window icon
        self.setWindowIcon(QIcon('icon.png'))

        self.setWindowTitle("Email Management System - Main Interface")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Removed the Generate Script Section as per your request

        # Manage Email Templates Button
        self.manage_templates_button = QPushButton("Manage Email Templates", self)
        self.manage_templates_button.clicked.connect(self.manage_templates)
        layout.addWidget(self.manage_templates_button)

        # Configuration Settings Button
        self.config_settings_button = QPushButton("Configuration Settings", self)
        self.config_settings_button.clicked.connect(self.open_configuration_settings)
        layout.addWidget(self.config_settings_button)

        # Email Configuration Button
        self.email_config_button = QPushButton("Email Configuration", self)
        self.email_config_button.clicked.connect(self.open_email_configuration)
        layout.addWidget(self.email_config_button)

        self.setLayout(layout)

        # Load configuration buttons data from JSON
        self.load_config_buttons()

    def open_email_configuration(self):
        self.email_config_dialog = EmailConfigurationDialog()
        self.email_config_dialog.exec_()

    def load_config_buttons(self):
        try:
            with open('config_buttons.json', 'r') as file:
                self.config_buttons_data = json.load(file)
        except FileNotFoundError:
            self.config_buttons_data = []
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to decode JSON configuration file.")
            self.config_buttons_data = []

    def manage_templates(self):
        # Pass config_buttons_data to TemplateManager
        self.template_dialog = TemplateManager(self.config_buttons_data)
        self.template_dialog.exec_()

    def open_configuration_settings(self):
        self.config_dialog = ConfigurationSettings()
        self.config_dialog.exec_()
        # Reload the config_buttons_data after closing the settings
        self.load_config_buttons()


class ConfigurationSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration Settings")
        self.setGeometry(150, 150, 600, 500)

        # Set window icon
        self.setWindowIcon(QIcon('icon.png'))

        # Create layout and widgets
        layout = QVBoxLayout()

        # Load buttons from JSON file
        self.load_buttons_from_json()

        # Create a layout to hold buttons
        self.buttons_layout = QVBoxLayout()

        # Add tool buttons with edit/delete functionality
        for button_data in self.config_buttons_data:
            self.add_config_button(button_data['name'], button_data['text'])

        # Add the buttons_layout to the main layout
        layout.addLayout(self.buttons_layout)

        # Add new button
        self.add_button = QPushButton("Add New Button", self)
        self.add_button.clicked.connect(self.add_new_button)
        layout.addWidget(self.add_button)

        # Set layout
        self.setLayout(layout)

    def load_buttons_from_json(self):
        # Load the button configuration from the JSON file
        try:
            with open('config_buttons.json', 'r') as file:
                self.config_buttons_data = json.load(file)
        except FileNotFoundError:
            # If the file doesn't exist, start with an empty list
            self.config_buttons_data = []
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to decode JSON configuration file.")
            self.config_buttons_data = []

    def save_buttons_to_json(self):
        # Save the button configuration to the JSON file
        with open('config_buttons.json', 'w') as file:
            json.dump(self.config_buttons_data, file, indent=4)

    def add_config_button(self, name, text):
        button_layout = QHBoxLayout()

        tool_button = QToolButton(self)
        tool_button.setText(name)
        tool_button.setPopupMode(QToolButton.MenuButtonPopup)
        button_menu = QMenu(self)

        edit_action = button_menu.addAction("Edit")
        edit_action.triggered.connect(lambda checked, b=tool_button: self.edit_button(b))

        delete_action = button_menu.addAction("Delete")
        delete_action.triggered.connect(lambda checked, b=tool_button: self.delete_button(b))

        tool_button.setMenu(button_menu)
        button_layout.addWidget(tool_button)
        self.buttons_layout.addLayout(button_layout)

    def edit_button(self, button):
        name = button.text()
        # Find the button data
        for button_data in self.config_buttons_data:
            if button_data['name'] == name:
                current_text = button_data['text']
                break
        else:
            current_text = ""

        # Prompt for new button name
        new_name, ok = QInputDialog.getText(self, "Edit Button", "Enter new name for the button:", QLineEdit.Normal, name)

        if ok and new_name:
            button.setText(new_name)
            button_data['name'] = new_name  # Update the name in the data

        # Prompt for the text associated with this button
        new_text, ok_text = QInputDialog.getMultiLineText(self, "Edit Button Text",
                                                          f"Enter the text for '{new_name}':", current_text)

        if ok_text:
            button_data['text'] = new_text  # Update the text in the data

        self.save_buttons_to_json()  # Save changes to JSON

    def delete_button(self, button):
        name = button.text()
        # Remove from the layout
        for i in reversed(range(self.buttons_layout.count())):
            item = self.buttons_layout.itemAt(i)
            if item.layout():
                sub_layout = item.layout()
                for j in range(sub_layout.count()):
                    sub_item = sub_layout.itemAt(j)
                    if sub_item.widget() == button:
                        # Remove the widget from the layout
                        button.deleteLater()
                        sub_layout.removeWidget(button)
                        break

        # Remove from the data
        self.config_buttons_data = [bd for bd in self.config_buttons_data if bd['name'] != name]
        self.save_buttons_to_json()  # Save changes to JSON

    def add_new_button(self):
        new_name, ok = QInputDialog.getText(self, "Add New Button", "Enter name for the new button:")
        if ok and new_name:
            new_text, ok_text = QInputDialog.getMultiLineText(self, "Add Button Text",
                                                              f"Enter the text for '{new_name}':", "")
            if ok_text:
                # Add to data
                new_button_data = {'name': new_name, 'text': new_text}
                self.config_buttons_data.append(new_button_data)
                self.save_buttons_to_json()  # Save changes to JSON

                # Add to UI
                self.add_config_button(new_name, new_text)

    def get_button_data(self):
        # Return the configuration buttons data
        return self.config_buttons_data

    def closeEvent(self, event):
        # Save changes when the dialog is closed
        self.save_buttons_to_json()
        event.accept()


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        else:
            return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        else:
            return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX

            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


class TemplateManager(QDialog):
    def __init__(self, config_buttons_data):
        super().__init__()
        self.setWindowTitle("Manage Email Templates")
        self.setGeometry(100, 100, 600, 700)  # Adjusted size if necessary

        # Set window icon
        self.setWindowIcon(QIcon('icon.png'))

        self.config_buttons_data = config_buttons_data

        layout = QVBoxLayout()

        # List to display existing templates
        self.template_list = QListWidget(self)
        self.template_list.itemClicked.connect(self.load_template)
        layout.addWidget(self.template_list)

        # Load existing templates from the database
        self.load_templates()

        # Fields for template name, subject, and body
        self.template_name_field = QLineEdit(self)
        self.template_name_field.setPlaceholderText("Template Name")
        layout.addWidget(self.template_name_field)

        self.template_subject_field = QLineEdit(self)
        self.template_subject_field.setPlaceholderText("Subject")
        layout.addWidget(self.template_subject_field)

        self.template_body_field = QTextEdit(self)
        self.template_body_field.setPlaceholderText("Body")
        layout.addWidget(self.template_body_field)

        # Field for recipient email address
        self.recipient_email_field = QLineEdit(self)
        self.recipient_email_field.setPlaceholderText("Recipient Email Address")
        layout.addWidget(self.recipient_email_field)

        # Layout for predefined text insertion buttons using FlowLayout
        button_layout = FlowLayout()
        for button_data in self.config_buttons_data:
            insert_button = QPushButton(button_data['name'], self)
            insert_button.clicked.connect(partial(self.insert_text, button_data['text']))
            button_layout.addWidget(insert_button)

        layout.addLayout(button_layout)

        # Layout for action buttons (Save, Delete, Send Email)
        action_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Template", self)
        self.save_button.clicked.connect(self.save_template)
        action_layout.addWidget(self.save_button)

        self.delete_button = QPushButton("Delete Template", self)
        self.delete_button.clicked.connect(self.delete_template)
        action_layout.addWidget(self.delete_button)

        self.send_button = QPushButton("Send Email", self)
        self.send_button.clicked.connect(self.send_email)
        action_layout.addWidget(self.send_button)

        layout.addLayout(action_layout)

        self.setLayout(layout)

    def load_templates(self):
        # Clear the current list
        self.template_list.clear()

        # Fetch templates from the database
        cursor.execute("SELECT id, name FROM Templates")
        templates = cursor.fetchall()

        # Add templates to the list
        for template in templates:
            item = QListWidgetItem(template[1])
            item.setData(Qt.UserRole, template[0])  # Store the template ID
            self.template_list.addItem(item)

    def load_template(self, item):
        template_id = item.data(Qt.UserRole)
        cursor.execute("SELECT name, subject, body FROM Templates WHERE id = ?", (template_id,))
        template = cursor.fetchone()
        if template:
            self.template_name_field.setText(template[0])
            self.template_subject_field.setText(template[1])
            self.template_body_field.setText(template[2])

    def save_template(self):
        name = self.template_name_field.text()
        subject = self.template_subject_field.text()
        body = self.template_body_field.toPlainText()

        if not name or not subject or not body:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")
            return

        # Check if a template with the same name exists
        cursor.execute("SELECT id FROM Templates WHERE name = ?", (name,))
        existing = cursor.fetchone()
        if existing:
            # Update the existing template
            cursor.execute("UPDATE Templates SET subject = ?, body = ? WHERE id = ?", (subject, body, existing[0]))
        else:
            # Insert a new template
            cursor.execute("INSERT INTO Templates (name, subject, body) VALUES (?, ?, ?)", (name, subject, body))
        conn.commit()

        QMessageBox.information(self, "Template Saved", "Template has been saved successfully.")
        self.load_templates()

    def delete_template(self):
        name = self.template_name_field.text()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please select a template to delete.")
            return

        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to delete the template '{name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            cursor.execute("DELETE FROM Templates WHERE name = ?", (name,))
            conn.commit()
            QMessageBox.information(self, "Template Deleted", "Template has been deleted.")

            # Clear the fields
            self.template_name_field.clear()
            self.template_subject_field.clear()
            self.template_body_field.clear()

            # Reload the templates list
            self.load_templates()

    def insert_text(self, text):
        self.template_body_field.insertPlainText(text)

    def send_email(self):
        recipient_email = self.recipient_email_field.text()
        subject = self.template_subject_field.text()
        body = self.template_body_field.toPlainText()

        if not recipient_email or not subject or not body:
            QMessageBox.warning(self, "Input Error", "Please fill in the recipient email, subject, and body.")
            return

        # Retrieve email configuration
        cursor.execute("SELECT smtp_server, smtp_port, username, password, use_tls, use_ssl FROM EmailConfig ORDER BY id DESC LIMIT 1")
        config = cursor.fetchone()
        if not config:
            QMessageBox.warning(self, "Configuration Error", "Email configuration not found. Please configure email settings.")
            return

        smtp_server, smtp_port, username_enc, password_enc, use_tls, use_ssl = config

        smtp_port = int(smtp_port)
        use_tls = bool(use_tls)
        use_ssl = bool(use_ssl)

        # Decrypt username and password
        username = cipher_suite.decrypt(username_enc.encode()).decode()
        password = cipher_suite.decrypt(password_enc.encode()).decode()
        sender_email = username

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            # Set up the SMTP server and send the email
            if use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
                server.login(username, password)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                server.login(username, password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()

            QMessageBox.information(self, "Email Sent", f"Email has been sent to {recipient_email}.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while sending the email: {str(e)}")


class EmailConfigurationDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Email Configuration")
        self.setGeometry(200, 200, 400, 300)

        # Set window icon
        self.setWindowIcon(QIcon('icon.png'))

        # Create layout and widgets
        layout = QVBoxLayout()

        self.smtp_server_field = QLineEdit(self)
        self.smtp_server_field.setPlaceholderText("SMTP Server")
        layout.addWidget(self.smtp_server_field)

        self.smtp_port_field = QLineEdit(self)
        self.smtp_port_field.setPlaceholderText("SMTP Port")
        layout.addWidget(self.smtp_port_field)

        self.username_field = QLineEdit(self)
        self.username_field.setPlaceholderText("Username")
        layout.addWidget(self.username_field)

        self.password_field = QLineEdit(self)
        self.password_field.setPlaceholderText("Password")
        self.password_field.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_field)

        self.use_tls_checkbox = QCheckBox("Use TLS", self)
        layout.addWidget(self.use_tls_checkbox)

        self.use_ssl_checkbox = QCheckBox("Use SSL", self)
        layout.addWidget(self.use_ssl_checkbox)

        # Load existing configuration
        self.load_configuration()

        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_configuration)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_configuration(self):
        # Load the existing configuration from the database
        cursor.execute("SELECT smtp_server, smtp_port, username, password, use_tls, use_ssl FROM EmailConfig ORDER BY id DESC LIMIT 1")
        config = cursor.fetchone()
        if config:
            smtp_server, smtp_port, username_enc, password_enc, use_tls, use_ssl = config
            self.smtp_server_field.setText(smtp_server)
            self.smtp_port_field.setText(str(smtp_port))
            username = cipher_suite.decrypt(username_enc.encode()).decode()
            password = cipher_suite.decrypt(password_enc.encode()).decode()
            self.username_field.setText(username)
            self.password_field.setText(password)
            self.use_tls_checkbox.setChecked(bool(use_tls))
            self.use_ssl_checkbox.setChecked(bool(use_ssl))

    def save_configuration(self):
        smtp_server = self.smtp_server_field.text()
        smtp_port = self.smtp_port_field.text()
        username = self.username_field.text()
        password = self.password_field.text()
        use_tls = int(self.use_tls_checkbox.isChecked())
        use_ssl = int(self.use_ssl_checkbox.isChecked())

        if not smtp_server or not smtp_port or not username or not password:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")
            return

        # Encrypt username and password
        username_enc = cipher_suite.encrypt(username.encode()).decode()
        password_enc = cipher_suite.encrypt(password.encode()).decode()

        smtp_port_int = int(smtp_port)  # Ensure port is an integer

        # Delete existing configuration
        cursor.execute("DELETE FROM EmailConfig")
        # Insert new configuration
        cursor.execute("INSERT INTO EmailConfig (smtp_server, smtp_port, username, password, use_tls, use_ssl) VALUES (?, ?, ?, ?, ?, ?)",
                       (smtp_server, smtp_port_int, username_enc, password_enc, use_tls, use_ssl))
        conn.commit()

        QMessageBox.information(self, "Configuration Saved", "Email configuration has been saved successfully.")
        self.accept()


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainProgram()
    window.show()
    sys.exit(app.exec_())
