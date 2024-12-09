import sys
import sqlite3

from PyQt5.QtWidgets import *
from datetime import datetime

button = """
    QPushButton {
        background-color: #4CAF50; /* Green */
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; /* Rounded corners */
    }
    QPushButton:hover {
        background-color: #3e8e41; /* Darker green on hover */
    }
"""

button2 = """
    QPushButton {
        background-color: #0499FA; /* Green */
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 10px; /* Rounded corners */
    }
    QPushButton:hover {
        background-color: #049FFF; /* Darker green on hover */
    }
"""

line = """
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

"""

box = """
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
"""

def register_user(name, lastName, email, passport, username, password, role):
    if not user_exists(username):
        conn = sqlite3.connect('bank.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO User (name, lastName, email, passport, username, password, role) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (name, lastName, email, passport, username, password, role))
        conn.commit()
        conn.close()
        QMessageBox.information(None, 'Успех', 'Регистрация прошла успешно!')
    else:
        QMessageBox.warning(None,'Ошибка', 'Логин занят')

def check_user(username, password):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, role FROM User WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    print(user)
    conn.close()
    return user

def user_exists(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM User')
    users = cursor.fetchall()
    conn.close()
    return users

def reset_user_password(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE User SET password = 123 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def get_transactions(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT amount, type, date FROM Transactions
                   JOIN Account AS SenderAccount ON Transactions.sender = SenderAccount.number 
                   JOIN Account AS ReceiverAccount ON Transactions.receiver = ReceiverAccount.number 
                   JOIN User ON SenderAccount.owner = User.username OR ReceiverAccount.owner = User.username 
                   WHERE User.username = ?""", (username,))
    transactions = cursor.fetchall()
    conn.close()
    return transactions

def get_accounts(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT number, balance FROM Account JOIN User ON User.username = owner WHERE User.username = ?", (username,))
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def get_all_requests():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM OpenAccountRequests")
    requests = cursor.fetchall()
    conn.close()
    return requests

def delete_user(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM User WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def create_bank_account(id, username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Account (balance, owner, address, isMain)VALUES (0, ?, 'idk', 0)", (username,))
    conn.commit()
    cursor.execute("DELETE FROM OpenAccountRequests WHERE requestID = ?", (id, ))
    conn.commit()
    conn.close()

def request_create_account(username):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO OpenAccountRequests (type, client)VALUES (?, ?)", ("Счет", username))
    conn.commit()
    conn.close()

def transfer_money(sender_account, receiver_account, amount):
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()

    # Check if accounts exist
    cursor.execute("SELECT balance FROM Account WHERE number = ?", (sender_account,))
    sender_balance = cursor.fetchone()
    if sender_balance is None:
        return False
    sender_balance = sender_balance[0]

    cursor.execute("SELECT balance FROM Account WHERE number = ?", (receiver_account,))
    receiver_balance = cursor.fetchone()
    if receiver_balance is None:
        return False
    receiver_balance = receiver_balance[0]

    # Check sufficient balance
    if sender_balance < amount:
        return False

    # Update balances and log transaction
    cursor.execute("UPDATE Account SET balance = ? WHERE number = ?", (sender_balance - amount, sender_account))
    cursor.execute("UPDATE Account SET balance = ? WHERE number = ?", (receiver_balance + amount, receiver_account))
    cursor.execute(
        "INSERT INTO Transactions (sender, receiver, amount, type, date) VALUES (?, ?, ?, ?, ?)",
        (sender_account, receiver_account, amount, "Перевод", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    return True



# Окно регистрации
class RegistrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Регистрация')
        self.setFixedSize(400, 500)

        layout = QVBoxLayout()

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText('Имя')
        self.name_input.setStyleSheet(line)
        layout.addWidget(self.name_input)

        self.lastName_input = QLineEdit(self)
        self.lastName_input.setPlaceholderText('Фамилия')
        self.lastName_input.setStyleSheet(line)
        layout.addWidget(self.lastName_input)

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText('email')
        self.email_input.setStyleSheet(line)
        layout.addWidget(self.email_input)

        self.passport_input = QLineEdit(self)
        self.passport_input.setPlaceholderText('Паспорт')
        self.passport_input.setStyleSheet(line)
        layout.addWidget(self.passport_input)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText('Логин')
        self.username_input.setStyleSheet(line)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(line)
        layout.addWidget(self.password_input)

        self.roleBox = QComboBox(self)
        self.roleBox.addItem("Пользователь")
        self.roleBox.addItem("Сотрудник")
        self.roleBox.addItem("Админ")
        self.roleBox.setStyleSheet(box)
        layout.addWidget(self.roleBox)

        self.register_button = QPushButton('Зарегистрироваться', self)
        self.register_button.clicked.connect(self.register)
        self.register_button.setStyleSheet(button)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

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
        self.username_input.setStyleSheet(line)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(line)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton('Войти', self)
        self.login_button.clicked.connect(self.login)
        self.login_button.setStyleSheet(button)
        # self.login_button.setStyleSheet("background-color:rgb(0,0,0)")
        layout.addWidget(self.login_button)

        self.open_reg_button = QPushButton('Регистрация', self)
        self.open_reg_button.clicked.connect(self.open_reg)
        self.open_reg_button.setStyleSheet(button)
        layout.addWidget(self.open_reg_button)

        self.setLayout(layout)

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

    def open_main_window(self, username):
        self.main_window = MainWindow(username)
        self.main_window.show()
        self.close()

    def open_worker_window(self):
        self.worker_window = WorkerWindow()
        self.worker_window.show()
        self.close()

    def open_admin_window(self):
        self.admin_window = AdminWindow()
        self.admin_window.show()
        self.close()

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
        update_button = QPushButton("Обновить", clicked=self.update)
        update_button.setStyleSheet(button)
        account_layout.addWidget(update_button)
        label = QLabel("Номер счета:")
        label.setMaximumHeight(50)
        label.setStyleSheet("font-size: 18px;")
        account_layout.addWidget(label)
        self.account_number_box = QComboBox()
        self.accounts = dict()
        self.account_number_box.setStyleSheet(box)
        account_layout.addWidget(self.account_number_box)
        balance_button = QPushButton("Баланс", clicked=self.check_balance)
        balance_button.setStyleSheet(button)
        account_layout.addWidget(balance_button)
        create_account_button = QPushButton("Открыть счет", clicked=self.create_account)
        create_account_button.setStyleSheet(button)
        account_layout.addWidget(create_account_button)
        self.account_tab.setLayout(account_layout)

        # Transactions Tab
        transactions_layout = QVBoxLayout()
        self.transactions_list = QListWidget()  # Consider using QTableView for better organization
        transactions_layout.addWidget(self.transactions_list)
        self.transactions_tab.setLayout(transactions_layout)
        #transfer
        transfer_layout = QVBoxLayout()
        self.receicer_line = QLineEdit()
        self.receicer_line.setPlaceholderText("Счет получателя")
        self.receicer_line.setStyleSheet(line)
        transfer_layout.addWidget(self.receicer_line)

        self.amount_line = QLineEdit()
        self.amount_line.setStyleSheet(line)
        self.amount_line.setPlaceholderText("Сумма")
        transfer_layout.addWidget(self.amount_line)

        self.send_button = QPushButton("Перевести", clicked=self.transfer)
        self.send_button.setStyleSheet(button)
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

    # Placeholder functions - replace with your actual application logic
    def check_balance(self):
        account_number = self.account_number_box.currentText()
        if account_number:
            balance = self.accounts[account_number]
            QMessageBox.information(self, "Баланс", f"Ваш баланс: {balance}")

    def init_accounts(self):
        self.account_number_box.clear()
        accounts = get_accounts(self.username)
        for number, balance in accounts:
            self.accounts[str(number)] = balance
            self.account_number_box.addItem(str(number))

    def create_account(self):
        request_create_account(self.username)
        self.init_accounts()
        QMessageBox.information(self, 'Успех', 'Запрос на открытие счета отправлен!')

    def view_transactions(self):
        self.transactions_list.clear()
        transactions = get_transactions(self.username)
        for amount, type, date in transactions:
            item = QListWidgetItem(f"Сумма: {amount}\n Тип: {type}\n Дата: {date}\n")
            self.transactions_list.addItem(item)

    def update(self):
        self.init_accounts()
        self.view_transactions()

    def transfer(self):
        sender = self.account_number_box.currentText()
        receiver = self.receicer_line.text()
        amount = self.amount_line.text()
        if transfer_money(sender, receiver, int(amount)):
            QMessageBox.information(self, "Успех", "Перевод выполнен")
            self.update()
        else:
            QMessageBox.warning(self, "Ошибка", "Ошибка при переводе")


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
        self.usersBox.setStyleSheet(box)
        layout.addWidget(self.usersBox)

        self.load_users_button = QPushButton('Загрузить пользователей', self)
        self.load_users_button.clicked.connect(self.load_users)
        self.load_users_button.setStyleSheet(button2)
        layout.addWidget(self.load_users_button)


        self.reset_password_button = QPushButton('Сбросить пароль', self)
        self.reset_password_button.clicked.connect(self.reset_password)
        self.reset_password_button.setStyleSheet(button2)
        layout.addWidget(self.reset_password_button)

        self.deleteUserBtn = QPushButton("Удалить полльзователя", self)
        self.deleteUserBtn.clicked.connect(self.deleteUser)
        self.deleteUserBtn.setStyleSheet(button2)
        layout.addWidget(self.deleteUserBtn)

        self.setLayout(layout)

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

    def reset_password(self):
        reset_user_password(self.usersBox.currentText())

    def deleteUser(self):
        delete_user(self.usersBox.currentText())
        self.load_users()

# Окно администратора
class WorkerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Сотрудник')
        self.setFixedSize(400, 500)
        layout = QVBoxLayout()
        self.requests_list = QTextEdit(self)
        self.requests_list.setReadOnly(True)
        self.requests_list.setStyleSheet("font-size:18px")
        layout.addWidget(self.requests_list)

        self.requestsBox = QComboBox(self)
        self.requestsBox.setStyleSheet(box)
        layout.addWidget(self.requestsBox)

        self.load_requests_button = QPushButton('Загрузить запросы', self)
        self.load_requests_button.clicked.connect(self.load_requests)
        self.load_requests_button.setStyleSheet(button2)
        layout.addWidget(self.load_requests_button)

        self.allow_request_button = QPushButton('Разрешить запрос', self)
        self.allow_request_button.clicked.connect(self.allow_request)
        self.allow_request_button.setStyleSheet(button2)
        layout.addWidget(self.allow_request_button)

        self.add_client_button = QPushButton('Добавить нового клиента', self)
        self.add_client_button.clicked.connect(self.add_new_client)
        self.add_client_button.setStyleSheet(button2)
        layout.addWidget(self.add_client_button)

        self.setLayout(layout)

    def load_requests(self):
        self.requestsBox.clear()
        requests = get_all_requests()
        request_display = ""
        self.request_box_items = dict()

        for id, type, client in requests:
            request_display += f"ID: {id} Клиент: {client} Тип: {type}\n"
            self.request_box_items[str(id)] = client

        self.requests_list.setPlainText(request_display)
        self.requestsBox.addItems(self.request_box_items.keys())

    def allow_request(self):
        if len(self.requestsBox.currentText()):
            ID = self.requestsBox.currentText()
            username = self.request_box_items[self.requestsBox.currentText()]
            create_bank_account(ID, username)
            self.load_requests()


    def add_new_client(self):
        self.reg_window = RegistrationWindow()
        self.reg_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())