import flet as ft
import sqlite3
import hashlib
import secrets
import socket
import threading
import json
import uuid

from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen


# ============================================================
# SAFEPAY
# Local Network Payment Simulator
# ============================================================

APP_NAME = "safepay"
PORT = 8765
STARTING_BALANCE = 10000.0
DB_FILE = "safepay.db"


# ============================================================
# SECURITY
# ============================================================

def hash_password(password):
    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        150000
    )

    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):
    try:
        salt_hex, hash_hex = stored.split(":")

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            150000
        )

        return secrets.compare_digest(
            actual,
            expected
        )

    except Exception:
        return False


# ============================================================
# DATABASE
# ============================================================

class Database:

    def __init__(self):

        self.lock = threading.RLock()

        self.db = sqlite3.connect(
            DB_FILE,
            check_same_thread=False
        )

        self.db.row_factory = sqlite3.Row

        self.create_tables()

    def execute(
        self,
        sql,
        params=(),
        fetch=False
    ):

        with self.lock:

            cursor = self.db.cursor()

            cursor.execute(
                sql,
                params
            )

            self.db.commit()

            if fetch:
                return cursor.fetchall()

            return cursor

    # --------------------------------------------------------

    def create_tables(self):

        self.execute("""
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                device_id TEXT NOT NULL,
                name TEXT NOT NULL,
                upi_id TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                balance REAL NOT NULL
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                person_name TEXT NOT NULL,
                person_upi TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS pending_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                sender_name TEXT NOT NULL,
                sender_upi TEXT NOT NULL,
                sender_ip TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

    # --------------------------------------------------------

    def account(self):

        rows = self.execute(
            "SELECT * FROM account WHERE id=1",
            fetch=True
        )

        if not rows:
            return None

        return dict(rows[0])

    # --------------------------------------------------------

    def create_account(
        self,
        name,
        upi,
        password
    ):

        try:

            self.execute("""
                INSERT INTO account
                (
                    id,
                    device_id,
                    name,
                    upi_id,
                    password_hash,
                    balance
                )
                VALUES
                (
                    1,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
            """, (
                str(uuid.uuid4()),
                name,
                upi,
                hash_password(password),
                STARTING_BALANCE
            ))

            return True

        except sqlite3.IntegrityError:

            return False

    # --------------------------------------------------------

    def verify_login(self, password):

        user = self.account()

        if not user:
            return False

        return verify_password(
            password,
            user["password_hash"]
        )

    # --------------------------------------------------------

    def change_password(self, password):

        self.execute("""
            UPDATE account
            SET password_hash=?
            WHERE id=1
        """, (
            hash_password(password),
        ))

    # --------------------------------------------------------

    def balance(self):

        user = self.account()

        if not user:
            return 0.0

        return float(
            user["balance"]
        )

    # --------------------------------------------------------

    def change_balance(self, amount):

        self.execute("""
            UPDATE account
            SET balance = balance + ?
            WHERE id=1
        """, (
            amount,
        ))

    # --------------------------------------------------------

    def add_transaction(
        self,
        transaction_id,
        transaction_type,
        person_name,
        person_upi,
        amount,
        status
    ):

        self.execute("""
            INSERT OR IGNORE INTO transactions
            (
                transaction_id,
                type,
                person_name,
                person_upi,
                amount,
                status,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id,
            transaction_type,
            person_name,
            person_upi,
            amount,
            status,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

    # --------------------------------------------------------

    def transactions(self):

        return self.execute("""
            SELECT *
            FROM transactions
            ORDER BY id DESC
        """, fetch=True)

    # --------------------------------------------------------

    def add_pending(
        self,
        transaction_id,
        sender_name,
        sender_upi,
        sender_ip,
        amount
    ):

        self.execute("""
            INSERT OR IGNORE INTO pending_payments
            (
                transaction_id,
                sender_name,
                sender_upi,
                sender_ip,
                amount,
                status,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id,
            sender_name,
            sender_upi,
            sender_ip,
            amount,
            "PENDING",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

    # --------------------------------------------------------

    def pending(self):

        return self.execute("""
            SELECT *
            FROM pending_payments
            WHERE status='PENDING'
            ORDER BY id DESC
        """, fetch=True)

    # --------------------------------------------------------

    def get_pending(self, transaction_id):

        rows = self.execute("""
            SELECT *
            FROM pending_payments
            WHERE transaction_id=?
        """, (
            transaction_id,
        ), fetch=True)

        if not rows:
            return None

        return dict(rows[0])

    # --------------------------------------------------------

    def update_pending(
        self,
        transaction_id,
        status
    ):

        self.execute("""
            UPDATE pending_payments
            SET status=?
            WHERE transaction_id=?
        """, (
            status,
            transaction_id
        ))

    # --------------------------------------------------------

    def transaction_status(
        self,
        transaction_id
    ):

        rows = self.execute("""
            SELECT *
            FROM transactions
            WHERE transaction_id=?
        """, (
            transaction_id,
        ), fetch=True)

        if not rows:
            return None

        return dict(rows[0])


db = Database()


# ============================================================
# NETWORK
# ============================================================

def get_local_ip():

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        s.connect(
            ("8.8.8.8", 80)
        )

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:

        try:
            return socket.gethostbyname(
                socket.gethostname()
            )
        except Exception:
            return "127.0.0.1"


# ============================================================
# NETWORK REQUEST
# ============================================================

def send_request(
    ip,
    endpoint,
    data=None
):

    try:

        url = (
            f"http://{ip}:{PORT}"
            f"{endpoint}"
        )

        body = None

        if data is not None:

            body = json.dumps(
                data
            ).encode("utf-8")

        request = Request(
            url,
            data=body,
            headers={
                "Content-Type":
                    "application/json"
            },
            method=(
                "POST"
                if body is not None
                else "GET"
            )
        )

        with urlopen(
            request,
            timeout=1.5
        ) as response:

            raw = response.read().decode(
                "utf-8"
            )

            return json.loads(raw)

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


# ============================================================
# LOCAL LAN SERVER
# ============================================================

class SafePayServer(
    BaseHTTPRequestHandler
):

    def log_message(
        self,
        format,
        *args
    ):
        return

    # --------------------------------------------------------

    def send_json(
        self,
        data,
        status=200
    ):

        raw = json.dumps(
            data
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Content-Length",
            str(len(raw))
        )

        self.end_headers()

        try:
            self.wfile.write(raw)
        except Exception:
            pass

    # --------------------------------------------------------

    def read_json(self):

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            if length <= 0:
                return {}

            raw = self.rfile.read(
                length
            )

            return json.loads(
                raw.decode("utf-8")
            )

        except Exception:

            return {}

    # --------------------------------------------------------

    def do_GET(self):

        path = self.path.split("?")[0]

        # PROFILE
        if path == "/profile":

            user = db.account()

            if not user:

                self.send_json({
                    "success": False,
                    "error": "No account"
                })

                return

            self.send_json({

                "success": True,

                "name":
                    user["name"],

                "upi_id":
                    user["upi_id"],

                "device_id":
                    user["device_id"]

            })

            return

        # PING
        if path == "/ping":

            self.send_json({
                "success": True,
                "app": APP_NAME,
                "port": PORT
            })

            return

        self.send_json({
            "success": False,
            "error": "Endpoint not found"
        }, 404)

    # --------------------------------------------------------

    def do_POST(self):

        path = self.path.split("?")[0]

        data = self.read_json()

        # ====================================================
        # PAYMENT REQUEST
        # ====================================================

        if path == "/payment/request":

            user = db.account()

            if not user:

                self.send_json({
                    "success": False,
                    "error": "Account unavailable"
                })

                return

            try:

                amount = float(
                    data.get(
                        "amount",
                        0
                    )
                )

            except Exception:

                self.send_json({
                    "success": False,
                    "error": "Invalid amount"
                })

                return

            if amount <= 0:

                self.send_json({
                    "success": False,
                    "error":
                        "Amount must be greater than zero"
                })

                return

            if amount > 1000000:

                self.send_json({
                    "success": False,
                    "error":
                        "Amount is too large"
                })

                return

            transaction_id = data.get(
                "transaction_id"
            )

            if not transaction_id:

                transaction_id = str(
                    uuid.uuid4()
                )

            sender_name = data.get(
                "sender_name",
                "Unknown"
            )

            sender_upi = data.get(
                "sender_upi",
                "unknown@safe"
            )

            sender_ip = self.client_address[0]

            # Don't allow duplicate pending request
            existing = db.get_pending(
                transaction_id
            )

            if existing:

                self.send_json({
                    "success": True,
                    "transaction_id":
                        transaction_id
                })

                return

            db.add_pending(

                transaction_id,

                sender_name,

                sender_upi,

                sender_ip,

                amount
            )

            self.send_json({

                "success": True,

                "transaction_id":
                    transaction_id

            })

            return

        # ====================================================
        # ACCEPT PAYMENT
        # ====================================================

        if path == "/payment/accept":

            transaction_id = data.get(
                "transaction_id"
            )

            if not transaction_id:

                self.send_json({
                    "success": False,
                    "error":
                        "Missing transaction ID"
                })

                return

            payment = db.get_pending(
                transaction_id
            )

            if not payment:

                self.send_json({
                    "success": False,
                    "error":
                        "Payment request not found"
                })

                return

            if payment["status"] != "PENDING":

                self.send_json({
                    "success": False,
                    "error":
                        "Payment already processed"
                })

                return

            amount = float(
                payment["amount"]
            )

            # The receiver receives money.
            db.change_balance(
                amount
            )

            db.update_pending(
                transaction_id,
                "ACCEPTED"
            )

            db.add_transaction(

                transaction_id,

                "RECEIVED",

                payment[
                    "sender_name"
                ],

                payment[
                    "sender_upi"
                ],

                amount,

                "SUCCESS"
            )

            self.send_json({
                "success": True,
                "status": "ACCEPTED"
            })

            return

        # ====================================================
        # REJECT PAYMENT
        # ====================================================

        if path == "/payment/reject":

            transaction_id = data.get(
                "transaction_id"
            )

            if not transaction_id:

                self.send_json({
                    "success": False,
                    "error":
                        "Missing transaction ID"
                })

                return

            payment = db.get_pending(
                transaction_id
            )

            if not payment:

                self.send_json({
                    "success": False,
                    "error":
                        "Payment request not found"
                })

                return

            if payment["status"] != "PENDING":

                self.send_json({
                    "success": False,
                    "error":
                        "Payment already processed"
                })

                return

            db.update_pending(
                transaction_id,
                "REJECTED"
            )

            self.send_json({
                "success": True,
                "status": "REJECTED"
            })

            return

        # ====================================================

        self.send_json({
            "success": False,
            "error": "Unknown endpoint"
        }, 404)


# ============================================================
# START SERVER
# ============================================================

def start_server():

    try:

        server = ThreadingHTTPServer(
            ("0.0.0.0", PORT),
            SafePayServer
        )

        print()
        print("==============================")
        print("          SAFEPAY")
        print("==============================")
        print()
        print(
            "LAN IP:",
            get_local_ip()
        )
        print(
            "PORT:",
            PORT
        )
        print()
        print(
            f"http://{get_local_ip()}:{PORT}"
        )
        print()

        server.serve_forever()

    except OSError as error:

        print(
            "Could not start LAN server:",
            error
        )

    except Exception as error:

        print(
            "Server error:",
            error
        )


threading.Thread(
    target=start_server,
    daemon=True
).start()


# ============================================================
# FLET APPLICATION
# ============================================================

def main(page: ft.Page):

    page.title = "SafePay"

    page.theme_mode = ft.ThemeMode.DARK

    page.padding = 0

    page.bgcolor = "#0B0F14"

    try:
        page.window.width = 430
        page.window.height = 800
    except Exception:
        pass

    # --------------------------------------------------------
    # HELPER
    # --------------------------------------------------------

    def message(
        title,
        text
    ):

        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(text),
            actions=[
                ft.TextButton(
                    content="OK",
                    on_click=lambda e:
                        page.pop_dialog()
                )
            ]
        )

        page.show_dialog(dialog)

    # --------------------------------------------------------

    def clear():

        page.controls.clear()

    # --------------------------------------------------------

    def primary_button(
        text,
        function
    ):

        return ft.Button(
            content=text,
            on_click=function,
            width=350,
            height=50,
            bgcolor="#19A974",
            color="#FFFFFF"
        )

    # --------------------------------------------------------

    def secondary_button(
        text,
        function
    ):

        return ft.OutlinedButton(
            content=text,
            on_click=function,
            width=350,
            height=48
        )

    # ========================================================
    # REGISTER
    # ========================================================

    def register():

        clear()

        name = ft.TextField(
            label="Full Name",
            width=350
        )

        upi = ft.TextField(
            label="SafePay ID",
            hint_text="name@safe",
            width=350
        )

        password = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=350
        )

        confirm = ft.TextField(
            label="Confirm Password",
            password=True,
            can_reveal_password=True,
            width=350
        )

        def create(e):

            n = name.value.strip()

            u = upi.value.strip().lower()

            p = password.value

            c = confirm.value

            if not n:

                message(
                    "Error",
                    "Enter your name."
                )

                return

            if "@" not in u:

                message(
                    "Error",
                    "Use an ID such as name@safe."
                )

                return

            if len(p) < 6:

                message(
                    "Error",
                    "Password must contain at least 6 characters."
                )

                return

            if p != c:

                message(
                    "Error",
                    "Passwords do not match."
                )

                return

            if db.account():

                message(
                    "Account Exists",
                    "This device already has an account."
                )

                return

            if not db.create_account(
                n,
                u,
                p
            ):

                message(
                    "Error",
                    "Could not create the account."
                )

                return

            home()

        page.add(

            ft.SafeArea(

                content=ft.Container(

                    padding=30,

                    content=ft.Column(

                        horizontal_alignment=
                            ft.CrossAxisAlignment.CENTER,

                        spacing=15,

                        controls=[

                            ft.Container(
                                height=25
                            ),

                            ft.Text(
                                "SafePay",
                                size=40,
                                weight=
                                    ft.FontWeight.BOLD,
                                color="#19A974"
                            ),

                            ft.Text(
                                "Create your local payment account",
                                size=15
                            ),

                            ft.Container(
                                height=10
                            ),

                            name,

                            upi,

                            password,

                            confirm,

                            ft.Container(
                                height=10
                            ),

                            primary_button(
                                "CREATE ACCOUNT",
                                create
                            )
                        ]
                    )
                )
            )
        )

        page.update()

    # ========================================================
    # LOGIN
    # ========================================================

    def login():

        clear()

        password = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=350
        )

        def do_login(e):

            if db.verify_login(
                password.value
            ):

                home()

            else:

                message(
                    "Login Failed",
                    "Incorrect password."
                )

        page.add(

            ft.SafeArea(

                content=ft.Container(

                    padding=30,

                    content=ft.Column(

                        horizontal_alignment=
                            ft.CrossAxisAlignment.CENTER,

                        spacing=18,

                        controls=[

                            ft.Container(
                                height=40
                            ),

                            ft.Text(
                                "SafePay",
                                size=42,
                                weight=
                                    ft.FontWeight.BOLD,
                                color="#19A974"
                            ),

                            ft.Text(
                                "Local Network Payment Simulator"
                            ),

                            ft.Container(
                                height=15
                            ),

                            password,

                            primary_button(
                                "LOGIN",
                                do_login
                            ),

                            ft.TextButton(
                                content="CREATE NEW ACCOUNT",
                                on_click=
                                    lambda e:
                                        register()
                            )
                        ]
                    )
                )
            )
        )

        page.update()

    # ========================================================
    # HOME
    # ========================================================

    def home():

        clear()

        user = db.account()

        if not user:

            register()

            return

        balance_text = ft.Text(
            f"₹ {db.balance():,.2f}",
            size=38,
            weight=ft.FontWeight.BOLD,
            color="#19A974"
        )

        def refresh_balance(e=None):

            balance_text.value = (
                f"₹ {db.balance():,.2f}"
            )

            page.update()

        page.add(

            ft.SafeArea(

                content=ft.Container(

                    padding=20,

                    content=ft.Column(

                        spacing=14,

                        scroll=ft.ScrollMode.AUTO,

                        controls=[

                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "SafePay",
                                        size=32,
                                        weight=
                                            ft.FontWeight.BOLD,
                                        color="#19A974"
                                    )
                                ]
                            ),

                            ft.Text(
                                "Available Balance",
                                size=14
                            ),

                            balance_text,

                            ft.Container(
                                padding=20,
                                bgcolor="#151B23",
                                border_radius=15,

                                content=ft.Column([
                                    ft.Text(
                                        user["name"],
                                        size=20,
                                        weight=
                                            ft.FontWeight.BOLD
                                    ),

                                    ft.Text(
                                        user["upi_id"]
                                    ),

                                    ft.Text(
                                        "● LOCAL NETWORK",
                                        size=12,
                                        color="#19A974"
                                    ),

                                    ft.Text(
                                        "IP: "
                                        + get_local_ip(),
                                        size=11
                                    )
                                ])
                            ),

                            primary_button(
                                "PAY PEOPLE NEARBY",
                                lambda e:
                                    nearby()
                            ),

                            secondary_button(
                                "PAYMENT REQUESTS",
                                lambda e:
                                    requests()
                            ),

                            secondary_button(
                                "TRANSACTION HISTORY",
                                lambda e:
                                    history()
                            ),

                            secondary_button(
                                "CHANGE PASSWORD",
                                lambda e:
                                    change_password()
                            ),

                            ft.TextButton(
                                content="LOG OUT",
                                on_click=
                                    lambda e:
                                        login()
                            )
                        ]
                    )
                )
            )
        )

        page.update()

    # ========================================================
    # NEARBY
    # ========================================================

    def nearby():

        clear()

        list_view = ft.Column(
            spacing=10
        )

        status = ft.Text(
            "Scanning your local network..."
        )

        results_container = ft.Container(
            height=500,
            content=ft.ListView(
                controls=[]
            )
        )

        def scan(e=None):

            status.value = (
                "Scanning local network..."
            )

            list_view.controls.clear()

            results_container.content = ft.ListView(
                controls=list_view.controls
            )

            page.update()

            local = get_local_ip()

            parts = local.split(".")

            if len(parts) != 4:

                status.value = (
                    "Could not determine your local network."
                )

                page.update()

                return

            found = []

            def worker():

                # Use a shorter timeout and parallel requests
                # so the scan does not take several minutes.

                from concurrent.futures import (
                    ThreadPoolExecutor,
                    as_completed
                )

                def check_ip(i):

                    ip = (
                        f"{parts[0]}."
                        f"{parts[1]}."
                        f"{parts[2]}."
                        f"{i}"
                    )

                    if ip == local:
                        return None

                    result = send_request(
                        ip,
                        "/profile"
                    )

                    if result.get("success"):

                        return (
                            ip,
                            result
                        )

                    return None

                with ThreadPoolExecutor(
                    max_workers=32
                ) as executor:

                    futures = [
                        executor.submit(
                            check_ip,
                            i
                        )
                        for i in range(1, 255)
                    ]

                    for future in as_completed(
                        futures
                    ):

                        try:

                            result = future.result()

                            if result:

                                found.append(
                                    result
                                )

                        except Exception:
                            pass

                found.sort(
                    key=lambda item:
                        item[1].get(
                            "name",
                            ""
                        ).lower()
                )

                list_view.controls.clear()

                if not found:

                    status.value = (
                        "No SafePay users found.\n"
                        "Make sure the other device is "
                        "on the same Wi-Fi/LAN."
                    )

                else:

                    status.value = (
                        f"{len(found)} "
                        "SafePay user(s) found."
                    )

                    for ip, user in found:

                        def pay_click(
                            e,
                            ip=ip,
                            user=user
                        ):

                            pay(
                                ip,
                                user
                            )

                        list_view.controls.append(

                            ft.Container(

                                padding=15,

                                bgcolor="#151B23",

                                border_radius=15,

                                content=ft.Column([

                                    ft.Text(
                                        user["name"],
                                        size=21,
                                        weight=
                                            ft.FontWeight.BOLD
                                    ),

                                    ft.Text(
                                        user["upi_id"]
                                    ),

                                    ft.Text(
                                        "● Same Network",
                                        size=13,
                                        color="#19A974"
                                    ),

                                    ft.Text(
                                        ip,
                                        size=11
                                    ),

                                    ft.Container(
                                        height=5
                                    ),

                                    primary_button(
                                        "PAY",
                                        pay_click
                                    )
                                ])
                            )
                        )

                results_container.content = ft.ListView(
                    controls=list_view.controls,
                    spacing=10
                )

                page.update()

            threading.Thread(
                target=worker,
                daemon=True
            ).start()

        page.add(

            ft.SafeArea(

                content=ft.Container(

                    padding=20,

                    content=ft.Column([

                        ft.Text(
                            "People Nearby",
                            size=30,
                            weight=
                                ft.FontWeight.BOLD
                        ),

                        status,

                        ft.Divider(),

                        results_container,

                        ft.Row([

                            ft.Button(
                                content="REFRESH",
                                on_click=scan
                            ),

                            ft.TextButton(
                                content="BACK",
                                on_click=
                                    lambda e:
                                        home()
                            )
                        ])
                    ])
                )
            )
        )

        page.update()

        scan()

    # ========================================================
    # PAY
    # ========================================================

    def pay(
        ip,
        user
    ):

        clear()

        amount = ft.TextField(
            label="Amount",
            prefix_text="₹ ",
            width=350,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        note = ft.TextField(
            label="Note (optional)",
            width=350
        )

        def send(e):

            try:

                value = float(
                    amount.value.strip()
                )

            except Exception:

                message(
                    "Error",
                    "Enter a valid amount."
                )

                return

            if value <= 0:

                message(
                    "Error",
                    "Amount must be greater than zero."
                )

                return

            if value > db.balance():

                message(
                    "Payment Failed",
                    "Insufficient balance."
                )

                return

            account = db.account()

            transaction_id = str(
                uuid.uuid4()
            )

            result = send_request(

                ip,

                "/payment/request",

                {
                    "transaction_id":
                        transaction_id,

                    "sender_name":
                        account["name"],

                    "sender_upi":
                        account["upi_id"],

                    "amount":
                        value,

                    "note":
                        note.value.strip()
                }
            )

            if not result.get(
                "success"
            ):

                message(
                    "Payment Failed",
                    result.get(
                        "error",
                        "Receiver unavailable."
                    )
                )

                return

            # Reserve the money locally.
            db.change_balance(
                -value
            )

            db.add_transaction(

                transaction_id,

                "SENT",

                user["name"],

                user["upi_id"],

                value,

                "PENDING"
            )

            message(
                "Payment Request Sent",
                (
                    f"₹{value:,.2f} payment request "
                    f"sent to {user['name']}.\n\n"
                    "The receiver must accept it."
                )
            )

            home()

        page.add(

            ft.SafeArea(

                content=ft.Container(

                    padding=30,

                    content=ft.Column(

                        spacing=15,

                        controls=[

                            ft.Text(
                                "Send Payment",
                                size=30,
                                weight=
                                    ft.FontWeight.BOLD
                            ),

                            ft.Container(
                                padding=18,
                                bgcolor="#151B23",
                                border_radius=15,

                                content=ft.Column([

                                    ft.Text(
                                        user["name"],
                                        size=23,
                                        weight=
                                            ft.FontWeight.BOLD
                                    ),

                                    ft.Text(
                                        user["upi_id"]
                                    ),

                                    ft.Text(
                                        "● Same Network",
                                        color="#19A974"
                                    )
                                ])
                            ),

                            ft.Divider(),

                            amount,

                            note,

                            primary_button(
                                "SEND PAYMENT REQUEST",
                                send
                            ),

                            ft.TextButton(
                                content="CANCEL",
                                on_click=
                                    lambda e:
                                        nearby()
                            )
                        ]
                    )
                )
            )
        )

        page.update()

    # ========================================================
    # PAYMENT REQUESTS
    # ========================================================

    def requests():

        clear()

        list_view = ft.Column(
            spacing=10
        )

        results_container = ft.Container(
            height=550,
            content=ft.ListView(
                controls=[]
            )
        )

        def refresh(e=None):

            list_view.controls.clear()

            payments = db.pending()

            if not payments:

                list_view.controls.append(

                    ft.Container(
                        padding=20,

                        content=ft.Text(
                            "No pending payment requests.",
                            size=16
                        )
                    )
                )

            for payment in payments:

                transaction_id = (
                    payment[
                        "transaction_id"
                    ]
                )

                amount = float(
                    payment["amount"]
                )

                sender = payment[
                    "sender_name"
                ]

                sender_upi = payment[
                    "sender_upi"
                ]

                sender_ip = payment[
                    "sender_ip"
                ]

                def accept(
                    e,
                    transaction_id=
                        transaction_id,
                    amount=amount,
                    sender=sender,
                    sender_upi=sender_upi,
                    sender_ip=sender_ip
                ):

                    result = send_request(

                        sender_ip,

                        "/payment/accept",

                        {
                            "transaction_id":
                                transaction_id
                        }
                    )

                    if not result.get(
                        "success"
                    ):

                        message(
                            "Error",
                            result.get(
                                "error",
                                "Could not accept payment."
                            )
                        )

                        return

                    db.change_balance(
                        amount
                    )

                    db.update_pending(
                        transaction_id,
                        "ACCEPTED"
                    )

                    db.add_transaction(

                        transaction_id,

                        "RECEIVED",

                        sender,

                        sender_upi,

                        amount,

                        "SUCCESS"
                    )

                    message(
                        "Payment Received",
                        f"₹{amount:,.2f} received."
                    )

                    refresh()

                def reject(
                    e,
                    transaction_id=
                        transaction_id,
                    sender_ip=sender_ip
                ):

                    result = send_request(

                        sender_ip,

                        "/payment/reject",

                        {
                            "transaction_id":
                                transaction_id
                        }
                    )

                    if result.get(
                        "success"
                    ):

                        db.update_pending(
                            transaction_id,
                            "REJECTED"
                        )

                        message(
                            "Rejected",
                            "Payment request rejected."
                        )

                        refresh()

                    else:

                        message(
                            "Error",
                            result.get(
                                "error",
                                "Could not reject payment."
                            )
                        )

                list_view.controls.append(

                    ft.Container(

                        padding=15,

                        bgcolor="#151B23",

                        border_radius=15,

                        content=ft.Column([

                            ft.Text(
                                sender,
                                size=20,
                                weight=
                                    ft.FontWeight.BOLD
                            ),

                            ft.Text(
                                sender_upi
                            ),

                            ft.Text(
                                f"₹ {amount:,.2f}",
                                size=25,
                                weight=
                                    ft.FontWeight.BOLD,
                                color="#19A974"
                            ),

                            ft.Row([

                                ft.Button(
                                    content="ACCEPT",
                                    on_click=accept,
                                    bgcolor="#19A974",
                                    color="#FFFFFF"
                                ),

                                ft.TextButton(
                                    content="REJECT",
                                    on_click=reject
                                )
                            ])
                        ])
                    )
                )

            results_container.content = ft.ListView(
                controls=list_view.controls,
                spacing=10
            )

            page.update()

        page.add(

            ft.SafeArea(

                content=ft.Container(

                    padding=20,

                    content=ft.Column([

                        ft.Text(
                            "Payment Requests",
                            size=30,
                            weight=
                                ft.FontWeight.BOLD
                        ),

                        results_container,

                        ft.Row([

                            ft.Button(
                                content="REFRESH",
                                on_click=refresh
                            ),

                            ft.TextButton(
                                content="BACK",
                                on_click=
                                    lambda e:
                                        home()
                            )
                        ])
                    ])
                )
            )
        )

        page.update()

        refresh()

    # ========================================================
    # HISTORY
    # ========================================================

    def history():

        clear()

        items = []

        for transaction in db.transactions():

            typ = transaction[
                "type"
            ]

            amount = float(
                transaction["amount"]
            )

            person = transaction[
                "person_name"
            ]

            upi = transaction[
                "person_upi"
            ]

            status = transaction[
                "status"
            ]

            timestamp = transaction[
                "timestamp"
            ]

            if typ == "SENT":

                direction = "PAID"

            else:

                direction = "RECEIVED"

            items.append(

                ft.Container(

                    padding=15,

                    bgcolor="#151B23",

                    border_radius=15,

                    content=ft.Column([

                        ft.Row([

                            ft.Text(
                                direction,
                                weight=
                                    ft.FontWeight.BOLD
                            ),

                            ft.Container(
                                expand=True
                            ),

                            ft.Text(
                                "₹ "
                                f"{amount:,.2f}",
                                size=20,
                                weight=
                                    ft.FontWeight.BOLD
                            )
                        ]),

                        ft.Text(
                            person
                        ),

                        ft.Text(
                            upi,
                            size=13
                        ),

                        ft.Text(
                            status,
                            size=12,
                            color=(
                                "#19A974"
                                if status ==
                                    "SUCCESS"
                                else "#F5A623"
                            )
                        ),

                        ft.Text(
                            timestamp,
                            size=11
                        )
                    ])
                )
            )

        if not items:

            items.append(

                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "No transactions yet."
                    )
                )
            )

        page.add(

            ft.SafeArea(

                content=ft.Container(

                    padding=20,

                    content=ft.Column([

                        ft.Text(
                            "Transaction History",
                            size=30,
                            weight=
                                ft.FontWeight.BOLD
                        ),

                        ft.Container(
                            height=600,

                            content=ft.ListView(
                                controls=items,
                                spacing=10
                            )
                        ),

                        ft.TextButton(
                            content="BACK",
                            on_click=
                                lambda e:
                                    home()
                        )
                    ])
                )
            )
        )

        page.update()

    # ========================================================
    # CHANGE PASSWORD
    # ========================================================

    def change_password():

        clear()

        old = ft.TextField(
            label="Current Password",
            password=True,
            can_reveal_password=True,
            width=350
        )

        new = ft.TextField(
            label="New Password",
            password=True,
            can_reveal_password=True,
            width=350
        )

        confirm = ft.TextField(
            label="Confirm New Password",
            password=True,
            can_reveal_password=True,
            width=350
        )

        def change(e):

            if not db.verify_login(
                old.value
            ):

                message(
                    "Error",
                    "Current password is incorrect."
                )

                return

            if len(
                new.value
            ) < 6:

                message(
                    "Error",
                    "New password must have at least 6 characters."
                )

                return

            if new.value != confirm.value:

                message(
                    "Error",
                    "Passwords do not match."
                )

                return

            db.change_password(
                new.value
            )

            message(
                "Success",
                "Password changed successfully."
            )

            home()

        page.add(

            ft.SafeArea(

                content=ft.Container(

                    padding=30,

                    content=ft.Column([

                        ft.Text(
                            "Change Password",
                            size=30,
                            weight=
                                ft.FontWeight.BOLD
                        ),

                        old,

                        new,

                        confirm,

                        primary_button(
                            "CHANGE PASSWORD",
                            change
                        ),

                        ft.TextButton(
                            content="BACK",
                            on_click=
                                lambda e:
                                    home()
                        )
                    ])
                )
            )
        )

        page.update()

    # ========================================================
    # START
    # ========================================================

    if db.account():

        login()

    else:

        register()


# ============================================================
# RUN CURRENT FLET
# ============================================================

if __name__ == "__main__":
    ft.run(main)
