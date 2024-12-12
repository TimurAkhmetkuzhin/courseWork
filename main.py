import sys
import sqlite3
import hashlib

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import *
from datetime import datetime

#Для создания базы данных
def create_db():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "Account" (
            "number" INTEGER PRIMARY KEY AUTOINCREMENT,
            "balance" INTEGER NOT NULL,
            "owner" TEXT NOT NULL,
            "address" TEXT NOT NULL,
            "status" TEXT NOT NULL,
            "openDate" TEXT NOT NULL,
            "deleteDate" TEXT,
            FOREIGN KEY("owner") REFERENCES "User"("username")
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "DeleteAccountRequests" (
            "requestID" INTEGER PRIMARY KEY AUTOINCREMENT,
            "type" TEXT NOT NULL,
            "client" TEXT NOT NULL,
            "accID" INTEGER NOT NULL,
            "status" TEXT NOT NULL,
            "requestDate" TEXT NOT NULL,
            "answerDate" TEXT NOT NULL,
            FOREIGN KEY("client") REFERENCES "User"("username"),
            FOREIGN KEY("accID") REFERENCES "Account"("number")
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "OpenAccountRequests" (
            "requestID"	INTEGER NOT NULL,
            "type"	TEXT NOT NULL,
            "client"	TEXT NOT NULL,
            "status" TEXT NOT NULL,
            "requestDate" TEXT NOT NULL,
            "answerDate" TEXT NOT NULL,
            FOREIGN KEY("client") REFERENCES "User"("username"),
            PRIMARY KEY("requestID" AUTOINCREMENT)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "Transactions" (
            "transactionID" INTEGER PRIMARY KEY AUTOINCREMENT,
            "sender" INTEGER NOT NULL,
            "receiver" INTEGER NOT NULL,
            "amount" INTEGER NOT NULL,
            "type" TEXT NOT NULL,
            "date" TEXT NOT NULL,
            FOREIGN KEY("sender") REFERENCES "Account"("number"),
            FOREIGN KEY("receiver") REFERENCES "Account"("number")
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "UpBalance" (
            "requestID" INTEGER PRIMARY KEY AUTOINCREMENT,
            "accID" INTEGER NOT NULL,
            "type" TEXT NOT NULL,
            "amount" INTEGER NOT NULL,
            "status" TEXT NOT NULL,
            "requestDate" TEXT NOT NULL,
            "answerDate" TEXT NOT NULL,
            FOREIGN KEY("accID") REFERENCES "Account"("number")
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "User" (
            "name" TEXT NOT NULL,
            "lastName" TEXT NOT NULL,
            "email" TEXT NOT NULL,
            "passport" TEXT NOT NULL,
            "username" TEXT NOT NULL PRIMARY KEY,
            "password" TEXT NOT NULL,
            "role" TEXT NOT NULL,
            "status" TEXT NOT NULL,
            "registerDate" TEXT NOT NULL,
            "deleteDate" TEXT
        )
    """)

    conn.commit()
    conn.close()

#Для регистрации
def register_user(name, lastName, email, passport, username, password, role):
    hash = hashlib.new('sha256')
    hash.update(password.encode())
    password = hash.hexdigest()
    if not user_exists(username):
        conn = sqlite3.connect('bank.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO User (name, lastName, email, passport, username, password, role, status, registerDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (name, lastName, email, passport, username, password, role, "Активный", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        QMessageBox.information(None, 'Успех', 'Регистрация прошла успешно!')
    else:
        QMessageBox.warning(None,'Ошибка', 'Логин занят')

#Для авторизации
def check_user(username, password):
    hash = hashlib.new('sha256')
    hash.update(password.encode())
    password = hash.hexdigest()
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, role FROM User WHERE username = ? AND password = ? AND status != "Удален"', (username, password))
    user = cursor.fetchone()
    print(user)
    conn.close()
    return user

#Для проверки, существует ли логин
def user_exists(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

#Для получения всех пользователей
def get_all_users():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM User WHERE status != "Удален"')
    users = cursor.fetchall()
    conn.close()
    return users

#Для сброса пароля
def reset_user_password(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    hash = hashlib.new('sha256')
    hash.update("123".encode())
    cursor.execute('UPDATE User SET password = ? WHERE username = ?', (hash.hexdigest(), username))
    conn.commit()
    conn.close()

#Для получения всех транзакций
def get_transactions(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT amount, type, date FROM Transactions
                   JOIN Account ON Transactions.receiver = Account.number OR Transactions.sender = Account.number 
                   JOIN User ON Account.owner = User.username 
                   WHERE User.username = ?""", (username,))
    transactions = cursor.fetchall()
    conn.close()
    return transactions

#Для получения всех счетов
def get_accounts(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT number, balance FROM Account JOIN User ON User.username = owner WHERE User.username = ?", (username,))
    accounts = cursor.fetchall()
    conn.close()
    return accounts

#Для получения всех запросов на открытие счета
def get_open_requests():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT requestID, type, client FROM OpenAccountRequests WHERE status = 'В процессе'")
    requests = cursor.fetchall()
    conn.close()
    return requests

#Получение всех запросов на закрытие счета
def get_delete_requests():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT requestID, client, type, accID FROM DeleteAccountRequests WHERE status = 'В процессе'")
    requests = cursor.fetchall()
    conn.close()
    return requests

#Удаление пользователя
def delete_user(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE User SET status = ?, deleteDate = ? WHERE username = ?',
                   ("Удален", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
    conn.commit()
    conn.close()

#Открытия счета
def create_bank_account(id, username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Account (balance, owner, address, status, openDate)VALUES (0, ?, 'Москва', 'Активный', ?)",
                   (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    cursor.execute("UPDATE OpenAccountRequests SET answerDate = ?, status = ? WHERE requestID = ?",
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Разрешен", id))
    conn.commit()
    conn.close()

#Отклонить открытие счета
def reject_create_account(id):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE OpenAccountRequests SET answerDate = ?, status = ? WHERE requestID = ?",
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Отклонен", id))
    conn.commit()
    conn.close()

#Запрос на открытие счета
def request_create_account(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO OpenAccountRequests (type, client, status, requestDate, answerDate)VALUES (?, ?, ?, ?, ?)",
                   ("Открытие счета", username, "В процессе", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "-"))
    conn.commit()
    conn.close()

#Закрытие счета
def delete_account(id, acc_id):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE Account SET status = ? WHERE number = ?", ("Закрыт", acc_id,))
    conn.commit()
    cursor.execute("UPDATE DeleteAccountRequests SET status = ?, answerDate = ? WHERE requestID = ?",
                   ("Разрешен", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id))
    conn.commit()
    conn.close()

#Запрос на закрытие счета
def request_delete_account(username, id):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO DeleteAccountRequests (type, client, accID, status, requestDate, answerDate)VALUES (?, ?, ?, ?, ?, ?)",
                   ("Закрытие счета", username, id, "В процессе", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "-"))
    conn.commit()
    conn.close()

#Отклонить закрытие счета
def reject_delete_account(id):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE DeleteAccountRequests SET status = ?, answerDate = ? WHERE requestID = ?",
                   ("Отклонен", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id))
    conn.commit()
    conn.close()

#Запрос на пополнение счета
def up_balance_request(id, amount):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO UpBalance(accID, amount, type, status, requestDate, answerDate) VALUES(?, ?, ?, ?, ?, ?)",
                   (id, amount, "Пополнение", "В процессе", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "-"))
    conn.commit()
    conn.close()

#Разрешение пополнение счета
def allow_up_balance(id, accid, amount):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE Account SET balance = balance + ? WHERE number = ?", (amount, accid))
    conn.commit()
    cursor.execute(
        "INSERT INTO Transactions (sender, receiver, amount, type, date) VALUES (?, ?, ?, ?, ?)",
        ("Банк", accid, amount, "Пополнение", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    cursor.execute("UPDATE UpBalance SET status = ?, answerDate = ? WHERE requestID = ?",
                   ("Разрешен", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id))
    conn.commit()
    conn.close()

#Отклонить пополнение счета
def reject_up_balance(id):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE UpBalance SET status = ?, requestDate = ? WHERE requestID = ?",
                   ("Отклонен", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id))
    conn.commit()
    conn.close()

#Получить все запросы на пополнение счета
def get_up_balance_requests():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT requestID, accID, type, amount FROM UpBalance WHERE status = 'В процессе'")
    requests = cursor.fetchall()
    conn.close()
    return requests

#Перевод денег
def transfer_money(sender_account, receiver_account, amount):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()

    # Check if accounts exist
    cursor.execute("SELECT balance FROM Account WHERE number = ?", (sender_account,))
    sender_balance = cursor.fetchone()
    if sender_balance is None:
        return 1
    sender_balance = sender_balance[0]

    cursor.execute("SELECT balance FROM Account WHERE number = ?", (receiver_account,))
    receiver_balance = cursor.fetchone()
    if receiver_balance is None:
        return 2
    receiver_balance = receiver_balance[0]

    # Check sufficient balance
    if sender_balance < amount:
        return 3

    # Update balances and log transaction
    cursor.execute("UPDATE Account SET balance = ? WHERE number = ?", (sender_balance - amount, sender_account))
    cursor.execute("UPDATE Account SET balance = ? WHERE number = ?", (receiver_balance + amount, receiver_account))
    cursor.execute(
        "INSERT INTO Transactions (sender, receiver, amount, type, date) VALUES (?, ?, ?, ?, ?)",
        (sender_account, receiver_account, amount, "Перевод", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    return 0


# Окно регистрации
class RegistrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Регистрация')
        self.setFixedSize(400, 500)

        layout = QVBoxLayout()

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText('Имя')
        self.name_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.name_input)

        self.lastName_input = QLineEdit(self)
        self.lastName_input.setPlaceholderText('Фамилия')
        self.lastName_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.lastName_input)

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText('email')
        self.email_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.email_input)

        self.passport_input = QLineEdit(self)
        self.passport_input.setPlaceholderText('Паспорт')
        self.passport_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.passport_input)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText('Логин')
        self.username_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.password_input)

        self.roleBox = QComboBox(self)
        self.roleBox.addItem("Пользователь")
        self.roleBox.addItem("Сотрудник")
        self.roleBox.addItem("Админ")
        self.roleBox.setStyleSheet("""
    QComboBox {
        background-color: #f2f2f2; 
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
        font-size: 14px;
    }
    QComboBox::drop-down {
        border-left-width: 1px;
        border-left-color: darkgray;
        border-left-style: solid; 
        border-top-right-radius: 3px; 
        border-bottom-right-radius: 3px; 
    }
""")
        layout.addWidget(self.roleBox)

        self.register_button = QPushButton('Зарегистрироваться', self)
        self.register_button.clicked.connect(self.register)
        self.register_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    #Регистрация
    def register(self):
        name = self.name_input.text()
        lastName = self.lastName_input.text()
        email = self.email_input.text()
        passport = self.passport_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.roleBox.currentText()

        if not name or not lastName or not email or not passport or not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля.')
            return

        register_user(name, lastName, email, passport, username, password, role)

# Окно авторизации
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Авторизация')
        self.setFixedSize(400, 400)

        layout = QVBoxLayout()

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText('Имя пользователя')
        self.username_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.password_input)

        self.login_button = QPushButton('Войти', self)
        self.login_button.clicked.connect(self.login)
        self.login_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        # self.login_button.setStyleSheet("background-color:rgb(0,0,0)")
        layout.addWidget(self.login_button)

        self.open_reg_button = QPushButton('Регистрация', self)
        self.open_reg_button.clicked.connect(self.open_reg)
        self.open_reg_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        layout.addWidget(self.open_reg_button)

        self.setLayout(layout)

    #Авторизация
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля!')
        else:
            user = check_user(username, password)
            if user:
                QMessageBox.information(self, 'Успех', 'Авторизация прошла успешно!')
                if user[1] == "Пользователь":
                    self.open_main_window(user[0])
                elif user[1] == "Сотрудник":
                    self.open_worker_window()
                elif user[1] == "Админ":
                    self.open_admin_window()
            else:
                QMessageBox.warning(self, 'Ошибка', 'Неправильный логин или пароль.')

    #Открыть главное окно
    def open_main_window(self, username):
        self.main_window = MainWindow(username)
        self.main_window.show()
        self.close()

    #Открыть окно сотрудника
    def open_worker_window(self):
        self.worker_window = WorkerWindow()
        self.worker_window.show()
        self.close()

    #Открыть окно админа
    def open_admin_window(self):
        self.admin_window = AdminWindow()
        self.admin_window.show()
        self.close()

    #Открыть окно регситрации
    def open_reg(self):
        self.reg_window = RegistrationWindow()
        self.reg_window.show()


# Главное окно
class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle('Модуль')
        self.setGeometry(800, 300, 400, 500)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.username = username
        self.initUI()

    def initUI(self):
        # Create tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
    QTabBar::tab {
        min-width: 90px; 
        background-color: #f0f0f0; 
        font-size: 12px;
        color: #333; 
    }
    QTabBar::tab::selected {
        background-color: #4CAF50;
        font-size: 12px;
        color: #ffffff; 
    }
""")
        self.account_tab = QWidget()
        self.transactions_tab = QWidget()
        self.transactions_tab.setStyleSheet("font-size: 18px;")
        self.transfer_tab = QWidget()
        tabs.addTab(self.account_tab, "Счета")
        tabs.addTab(self.transactions_tab, "История")
        tabs.addTab(self.transfer_tab, "Переводы")

        # Account Tab
        account_layout = QVBoxLayout()

        label = QLabel("Номер счета:")
        label.setMaximumHeight(50)
        label.setStyleSheet("font-size: 18px;")
        account_layout.addWidget(label)

        self.account_number_box = QComboBox()
        self.accounts = dict()
        self.account_number_box.setStyleSheet("""
    QComboBox {
        background-color: #f2f2f2; 
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
        font-size: 14px;
    }
    QComboBox::drop-down {
        border-left-width: 1px;
        border-left-color: darkgray;
        border-left-style: solid; 
        border-top-right-radius: 3px; 
        border-bottom-right-radius: 3px; 
    }
""")
        account_layout.addWidget(self.account_number_box)

        balance_button = QPushButton("Баланс", clicked=self.check_balance)
        balance_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        account_layout.addWidget(balance_button)

        create_account_button = QPushButton("Открыть счет", clicked=self.create_account)
        create_account_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        account_layout.addWidget(create_account_button)

        up_balance_button = QPushButton("Пополнить счет", clicked=self.up_balance)
        up_balance_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        account_layout.addWidget(up_balance_button)

        delete_account_button = QPushButton("Закрыть счет", clicked=self.delete_account)
        delete_account_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        account_layout.addWidget(delete_account_button)
        self.account_tab.setLayout(account_layout)


        # Transactions Tab
        transactions_layout = QVBoxLayout()
        self.transactions_list = QListWidget()
        transactions_layout.addWidget(self.transactions_list)
        self.transactions_tab.setLayout(transactions_layout)

        #transfer
        transfer_layout = QVBoxLayout()
        self.receicer_line = QLineEdit()
        self.receicer_line.setPlaceholderText("Счет получателя")
        self.receicer_line.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        transfer_layout.addWidget(self.receicer_line)

        self.amount_line = QLineEdit()
        self.amount_line.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        self.amount_line.setPlaceholderText("Сумма")
        transfer_layout.addWidget(self.amount_line)

        self.send_button = QPushButton("Перевести", clicked=self.transfer)
        self.send_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        transfer_layout.addWidget(self.send_button)

        self.transfer_tab.setLayout(transfer_layout)

        # Main Layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addWidget(tabs)

        # Menu Bar (Optional)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('Выйти')
        fileMenu.addAction('Exit', self.close)

        self.init_accounts()
        self.view_transactions()

    #Проверить баланс счета
    def check_balance(self):
        if self.account_number_box.currentText():
            account_number = self.account_number_box.currentText()
            if account_number:
                balance = self.accounts[account_number]
                QMessageBox.information(self, "Баланс", f"Ваш баланс: {(balance / 100):.2f} рублей")
        else:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте счет")

    #Показать все счета
    def init_accounts(self):
        self.account_number_box.clear()
        accounts = get_accounts(self.username)
        for number, balance in accounts:
            self.accounts[str(number)] = balance
            self.account_number_box.addItem(str(number))

    #Открыть счет
    def create_account(self):
        request_create_account(self.username)
        self.init_accounts()
        QMessageBox.information(self, 'Успех', 'Запрос на открытие счета отправлен!')

    #Закрыть счет
    def delete_account(self):
        if self.account_number_box.currentText():
            request_delete_account(self.username, self.account_number_box.currentText())
            self.init_accounts()
            QMessageBox.information(self, 'Успех', 'Запрос на закрытие счета отправлен!')
        else:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте счет")

    #Показать историю
    def view_transactions(self):
        self.transactions_list.clear()
        transactions = get_transactions(self.username)
        for amount, type, date in transactions:
            item = QListWidgetItem(f"Сумма: {(amount / 100):.2f} руб.\n Тип: {type}\n Дата: {date}\n")
            self.transactions_list.addItem(item)

    #Обновить окно
    def update(self):
        self.init_accounts()
        self.view_transactions()

    #Перевод денег
    def transfer(self):
        if self.account_number_box.currentText():
            sender = self.account_number_box.currentText()
            receiver = self.receicer_line.text()
            amount = self.amount_line.text()
            state = transfer_money(sender, receiver, round(float(amount), 2) * 100)
            if state == 0:
                QMessageBox.information(self, "Успех", "Перевод выполнен")
                self.update()
            elif state == 1:
                QMessageBox.warning(self, "Ошибка", "Неизвестная ошибка")
                self.update()
            elif state == 2:
                QMessageBox.warning(self, "Ошибка", "Счета получателя не существует")
                self.update()
            elif state == 3:
                QMessageBox.warning(self, "Ошибка", "На счету недостаточно денег")
                self.update()

        else:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте счет")

    #Пополнить счет
    def up_balance(self):
        if self.account_number_box.currentText():
            self.up_balance_window = UpBalance(self.account_number_box.currentText())
            self.up_balance_window.show()
        else:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте счет")

#Окно пополнения счета
class UpBalance(QWidget):
    def __init__(self, account):
        super().__init__()
        self.setWindowTitle("Пополнение")
        self.setFixedSize(QSize(300, 300))
        self.account = account
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.amount_input = QLineEdit(self)
        self.amount_input.setPlaceholderText("Сумма")
        self.amount_input.setStyleSheet("""
    QLineEdit {
        background-color: #f0f0f0; /* Light gray background */
        border: 1px solid #ccc; /* Light gray border */
        border-radius: 10px; /* Rounded corners */
        padding: 5px;
        height:40px;
        font-size: 18px;
        color: #333; /* Dark gray text */
    }
    QLineEdit:focus {
        background-color: #fff; /* White background when focused */
        border: 1px solid #4CAF50; /* Green border when focused */
    }
    QLineEdit::placeholder {
        color: #999; /* Light gray placeholder text */
    }

""")
        layout.addWidget(self.amount_input)

        up_balance_button = QPushButton("Пополнить", clicked=self.up_balance)
        up_balance_button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: #3e8e41; 
    }
""")
        layout.addWidget(up_balance_button)

        self.setLayout(layout)

    #Пополнить счет
    def up_balance(self):
        amount = self.amount_input.text()
        up_balance_request(self.account, round(float(amount), 2) * 100)
        QMessageBox.information(self, "Успех", "Запрос на пополнение отправлен")


# Окно администратора
class AdminWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Админка')
        self.setFixedSize(400, 500)
        layout = QVBoxLayout()
        self.user_list = QTextEdit(self)
        self.user_list.setReadOnly(True)
        self.user_list.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.user_list)

        self.usersBox = QComboBox(self)
        self.usersBox.setStyleSheet("""
    QComboBox {
        background-color: #f2f2f2; 
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
        font-size: 14px;
    }
    QComboBox::drop-down {
        border-left-width: 1px;
        border-left-color: darkgray;
        border-left-style: solid; 
        border-top-right-radius: 3px; 
        border-bottom-right-radius: 3px; 
    }
""")
        layout.addWidget(self.usersBox)

        self.load_users_button = QPushButton('Загрузить пользователей', self)
        self.load_users_button.clicked.connect(self.load_users)
        self.load_users_button.setStyleSheet("""
    QPushButton {
        background-color: #0499FA;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; 
    }
    QPushButton:hover {
        background-color: #049FFF;
    }
""")
        layout.addWidget(self.load_users_button)

        self.reset_password_button = QPushButton('Сбросить пароль', self)
        self.reset_password_button.clicked.connect(self.reset_password)
        self.reset_password_button.setStyleSheet("""
    QPushButton {
        background-color: #0499FA;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; 
    }
    QPushButton:hover {
        background-color: #049FFF;
    }
""")
        layout.addWidget(self.reset_password_button)

        self.deleteUserBtn = QPushButton("Удалить пользователя", self)
        self.deleteUserBtn.clicked.connect(self.deleteUser)
        self.deleteUserBtn.setStyleSheet("""
    QPushButton {
        background-color: #0499FA;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; 
    }
    QPushButton:hover {
        background-color: #049FFF;
    }
""")
        layout.addWidget(self.deleteUserBtn)

        self.setLayout(layout)

    #Загрузить информацию о пользователях
    def load_users(self):
        self.usersBox.clear()
        self.user_list.clear()
        users = get_all_users()
        users_display = ""
        users_box_items = []

        for username in users:
            users_display += f"Логин: {username[0]}\n"
            users_box_items.append(username[0])

        self.user_list.setPlainText(users_display)
        self.usersBox.addItems(users_box_items)

    #Сбросить пароль
    def reset_password(self):
        if self.usersBox.currentText():
            reset_user_password(self.usersBox.currentText())

    #Удалить пользователя
    def deleteUser(self):
        if self.usersBox.currentText():
            delete_user(self.usersBox.currentText())
            self.load_users()

# Окно сотрудника
class WorkerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Сотрудник')
        self.setFixedSize(400, 500)
        layout = QVBoxLayout()

        self.requests_list = QTextEdit(self)
        self.requests_list.setReadOnly(True)
        self.requests_list.setStyleSheet("font-size:18px")

        self.filter = QComboBox()
        self.filter.setStyleSheet("""
    QComboBox {
        background-color: #f2f2f2; 
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
        font-size: 14px;
    }
    QComboBox::drop-down {
        border-left-width: 1px;
        border-left-color: darkgray;
        border-left-style: solid; 
        border-top-right-radius: 3px; 
        border-bottom-right-radius: 3px; 
    }
""")
        self.filter.addItem("Все")
        self.filter.addItem("Пополнение")
        self.filter.addItem("Открытие")
        self.filter.addItem("Закрытие")
        self.filter.currentTextChanged.connect(self.load_requests)
        self.request_box_items = dict()

        layout.addWidget(self.filter)
        layout.addWidget(self.requests_list)

        self.requestsBox = QComboBox(self)
        self.requestsBox.setStyleSheet("""
    QComboBox {
        background-color: #f2f2f2; 
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
        font-size: 14px;
    }
    QComboBox::drop-down {
        border-left-width: 1px;
        border-left-color: darkgray;
        border-left-style: solid; 
        border-top-right-radius: 3px; 
        border-bottom-right-radius: 3px; 
    }
""")
        layout.addWidget(self.requestsBox)

        self.load_requests_button = QPushButton('Загрузить запросы', self)
        self.load_requests_button.clicked.connect(self.load_requests)
        self.load_requests_button.setStyleSheet("""
    QPushButton {
        background-color: #0499FA;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; 
    }
    QPushButton:hover {
        background-color: #049FFF;
    }
""")
        layout.addWidget(self.load_requests_button)

        btn_layout = QHBoxLayout()
        self.allow_request_button = QPushButton('Разрешить', self)
        self.allow_request_button.clicked.connect(self.allow_request)
        self.allow_request_button.setStyleSheet("""
    QPushButton {
        background-color: #0499FA;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; 
    }
    QPushButton:hover {
        background-color: #049FFF;
    }
""")
        btn_layout.addWidget(self.allow_request_button)

        self.reject_request_button = QPushButton('Отклонить', self)
        self.reject_request_button.clicked.connect(self.reject_request)
        self.reject_request_button.setStyleSheet("""
    QPushButton {
        background-color: #0499FA;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; 
    }
    QPushButton:hover {
        background-color: #049FFF;
    }
""")
        btn_layout.addWidget(self.reject_request_button)

        layout.addLayout(btn_layout)

        self.add_client_button = QPushButton('Добавить нового клиента', self)
        self.add_client_button.clicked.connect(self.add_new_client)
        self.add_client_button.setStyleSheet("""
    QPushButton {
        background-color: #0499FA;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; 
    }
    QPushButton:hover {
        background-color: #049FFF;
    }
""")
        layout.addWidget(self.add_client_button)

        self.setLayout(layout)

    #Загрузить все запросы
    def load_requests(self):
        self.requestsBox.clear()
        self.request_box_items.clear()
        request_display = ""

        if self.filter.currentText() == "Пополнение":
            up_balance_requests = get_up_balance_requests()
            for id, accid, type, amount in up_balance_requests:
                request_display += f"ID: {id}\nСумма: {amount / 100}\nТип: {type}\nАккаунт:{accid}\n\n"
                self.request_box_items[str(id)] = (amount, type, accid)
        elif self.filter.currentText() == "Открытие":
            open_requests = get_open_requests()
            for id, type, client in open_requests:
                request_display += f"ID: {id}\nКлиент: {client}\nТип: {type}\n\n"
                self.request_box_items[str(id)] = (client, type)
        elif self.filter.currentText() == "Закрытие":
            del_requests = get_delete_requests()
            for id, client, type, accID in del_requests:
                request_display += f"ID: {id}\nКлиент: {client}\nТип: {type}\nАккаунт:{accID}\n\n"
                self.request_box_items[str(id)] = (client, type, accID)
        else:
            up_balance_requests = get_up_balance_requests()
            open_requests = get_open_requests()
            del_requests = get_delete_requests()
            for id, type, client in open_requests:
                request_display += f"ID: {id}\nКлиент: {client}\nТип: {type}\n\n"
                self.request_box_items[str(id)] = (client, type)

            for id, client, type, accID in del_requests:
                request_display += f"ID: {id}\nКлиент: {client}\nТип: {type}\nАккаунт:{accID}\n\n"
                self.request_box_items[str(id)] = (client, type, accID)

            for id, accid, type, amount in up_balance_requests:
                request_display += f"ID: {id}\nСумма: {amount / 100}\nТип: {type}\nАккаунт:{accid}\n\n"
                self.request_box_items[str(id)] = (amount, type, accid)

        self.requests_list.setPlainText(request_display)
        self.requestsBox.addItems(self.request_box_items.keys())

    #Разрешить запрос
    def allow_request(self):
        if self.requestsBox.currentText():
            print(self.request_box_items[self.requestsBox.currentText()][1])
            if self.request_box_items[self.requestsBox.currentText()][1] == "Закрытие счета":
                ID = self.requestsBox.currentText()
                delete_account(ID, self.request_box_items[self.requestsBox.currentText()][2])
                self.load_requests()

            elif self.request_box_items[self.requestsBox.currentText()][1] == "Открытие счета":
                ID = self.requestsBox.currentText()
                username = self.request_box_items[self.requestsBox.currentText()][0]
                create_bank_account(ID, username)
                self.load_requests()

            elif self.request_box_items[self.requestsBox.currentText()][1] == "Пополнение":
                ID = self.requestsBox.currentText()
                amount = self.request_box_items[self.requestsBox.currentText()][0]
                accid = self.request_box_items[self.requestsBox.currentText()][2]
                allow_up_balance(ID, accid, amount)
                self.load_requests()

    #Отклонить запрос
    def reject_request(self):
        if self.requestsBox.currentText():
            if self.request_box_items[self.requestsBox.currentText()][1] == "Закрытие счета":
                ID = self.requestsBox.currentText()
                reject_delete_account(ID)
                self.load_requests()

            elif self.request_box_items[self.requestsBox.currentText()][1] == "Открытие счета":
                ID = self.requestsBox.currentText()
                reject_create_account(ID)
                self.load_requests()

            elif self.request_box_items[self.requestsBox.currentText()][1] == "Пополнение":
                ID = self.requestsBox.currentText()
                reject_up_balance(ID)
                self.load_requests()

    #Открыть окно регистрации
    def add_new_client(self):
        self.reg_window = RegistrationWindow()
        self.reg_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    create_db()
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())