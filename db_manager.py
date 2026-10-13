import sqlite3
from datetime import datetime

DB_FILE = "deddie_applications.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS applications")

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS applications
                   (
                       request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       request_type TEXT DEFAULT 'Νέα Αίτηση Σύνδεσης',
                       firstname TEXT,
                       lastname TEXT,
                       tax_id TEXT,
                       person_type TEXT,
                       city TEXT,
                       producer_type TEXT,
                       station_tech TEXT,
                       installed_power REAL,
                       max_power REAL,
                       compensation_type TEXT,
                       status TEXT DEFAULT 'ΥΠΟΒΟΛΗ ΑΙΤΗΣΗΣ',
                       termination_reason TEXT,
                       date_submitted TEXT,
                       date_non_binding TEXT,
                       date_final_offer TEXT,
                       date_rejection TEXT,
                       date_contract TEXT,
                       date_operation TEXT,
                       date_cancelled TEXT
                   )
                   """)

    # Triggers for Progress Stages
    stages = [
        ("trg_non_binding", "ΜΕ ΜΗ ΔΕΣΜΕΥΤΙΚΗ ΠΡΟΣΦΟΡΑ", "date_non_binding"),
        ("trg_final_offer", "ΜΕ ΟΡΙΣΤΙΚΗ ΠΡΟΣΦΟΡΑ", "date_final_offer"),
        ("trg_contract", "ΜΕ ΣΥΜΒΑΣΗ ΣΥΝΔΕΣΗΣ", "date_contract"),
        ("trg_operation", "ΣΕ ΛΕΙΤΟΥΡΓΙΑ", "date_operation")
    ]

    for trigger_name, status_value, date_column in stages:
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_name}
            AFTER UPDATE OF status ON applications
            WHEN NEW.status = '{status_value}'
            BEGIN
                UPDATE applications
                SET {date_column} = datetime('now', 'localtime')
                WHERE request_id = NEW.request_id;
            END;
        """)

    # Triggers for Termination Stages
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_rejection
        AFTER UPDATE OF status, termination_reason ON applications
        WHEN NEW.status = 'ΜΕ ΑΔΥΝΑΜΙΑ ΣΥΝΔΕΣΗΣ' AND NEW.termination_reason = 'ΑΠΟΡΡΙΨΗ'
        BEGIN
            UPDATE applications
            SET date_rejection = datetime('now', 'localtime')
            WHERE request_id = NEW.request_id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_cancelled
        AFTER UPDATE OF status, termination_reason ON applications
        WHEN NEW.status = 'ΜΕ ΑΔΥΝΑΜΙΑ ΣΥΝΔΕΣΗΣ' AND NEW.termination_reason = 'ΑΚΥΡΩΣΗ'
        BEGIN
            UPDATE applications
            SET date_cancelled = datetime('now', 'localtime')
            WHERE request_id = NEW.request_id;
        END;
    """)

    conn.commit()
    conn.close()
    print("Η νέα βάση δεδομένων ΑΠΕ αρχικοποιήθηκε!")


def save_new_application(firstname, lastname, tax_id, person_type,
                         city, producer_type, station_tech, installed_power,
                         max_power, compensation_type=None):

    conn = get_connection()
    cursor = conn.cursor()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
                   INSERT INTO applications (
                       firstname,
                       lastname,
                       tax_id,
                       person_type,
                       city,
                       producer_type,
                       station_tech,
                       installed_power,
                       max_power,
                       compensation_type,
                       status,
                       date_submitted
                   )
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   """,
                   (
                       firstname,
                       lastname,
                       tax_id,
                       person_type,
                       city,
                       producer_type,
                       station_tech,
                       float(installed_power),
                       float(max_power),
                       compensation_type,
                       'ΥΠΟΒΟΛΗ ΑΙΤΗΣΗΣ',
                       current_time
                   ))

    request_id = cursor.lastrowid

    conn.commit()
    conn.close()

    print(
        f"Η αίτηση καταχωρήθηκε επιτυχώς με Κωδικό Αίτησης: {request_id}"
    )

    return request_id


def get_application_status_by_request(request_id):

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM applications WHERE request_id = ?",
        (int(request_id),)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)

    return None


def update_application_status(request_id, stage_name):

    conn = get_connection()
    cursor = conn.cursor()

    status_map = {
        'non_binding': (
            'ΜΕ ΜΗ ΔΕΣΜΕΥΤΙΚΗ ΠΡΟΣΦΟΡΑ',
            None
        ),
        'final_offer': (
            'ΜΕ ΟΡΙΣΤΙΚΗ ΠΡΟΣΦΟΡΑ',
            None
        ),
        'contract': (
            'ΜΕ ΣΥΜΒΑΣΗ ΣΥΝΔΕΣΗΣ',
            None
        ),
        'operation': (
            'ΣΕ ΛΕΙΤΟΥΡΓΙΑ',
            None
        ),
        'rejection': (
            'ΜΕ ΑΔΥΝΑΜΙΑ ΣΥΝΔΕΣΗΣ',
            'ΑΠΟΡΡΙΨΗ'
        ),
        'cancelled': (
            'ΜΕ ΑΔΥΝΑΜΙΑ ΣΥΝΔΕΣΗΣ',
            'ΑΚΥΡΩΣΗ'
        )
    }

    if stage_name in status_map:
        new_status, term_reason = status_map[stage_name]

        query = """
            UPDATE applications
            SET status = ?, termination_reason = ?
            WHERE request_id = ?
        """

        cursor.execute(
            query,
            (new_status, term_reason, int(request_id))
        )

        conn.commit()

        reason_text = (
            f" (Αιτία: {term_reason})"
            if term_reason
            else ""
        )

        print(
            f"Η αίτηση {request_id} ενημερώθηκε σε: "
            f"{new_status}{reason_text}"
        )

    conn.close()

if __name__ == "__main__":
    init_db()