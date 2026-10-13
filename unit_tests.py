import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db_manager

def setup_test_db(tmp_path):

    test_db = tmp_path / "test_database.db"

    db_manager.DB_FILE = str(test_db)

    db_manager.init_db()

def create_test_application():
    return db_manager.save_new_application(
        firstname="Δημήτριος",
        lastname="Αθανασάκης",
        tax_id="139845620",
        person_type="Φυσικό Πρόσωπο",
        city="Ηράκλειο",
        producer_type="Αυτοπαραγωγός Ταυτοχρονισμένου Συμψηφισμού με αποζημίωση ηλεκτρικής ενέργειας",
        station_tech="Φωτοβολταϊκός σταθμός (ΦΒ)",
        installed_power=100,
        max_power=80,
        compensation_type="Απευθείας συμμετοχή στην αγορά"
    )


# Use Case 3

def test_UseCase3_save_and_get_application(tmp_path):

    setup_test_db(tmp_path)

    request_id = create_test_application()

    application = db_manager.get_application_status_by_request(
        request_id
    )

    assert application is not None
    assert application["request_id"] == request_id
    assert application["firstname"] == "Δημήτριος"
    assert application["lastname"] == "Αθανασάκης"
    assert application["tax_id"] == "139845620"
    assert application["status"] == "ΥΠΟΒΟΛΗ ΑΙΤΗΣΗΣ"
    assert application["date_submitted"] is not None


# Use Case 4

def test_UseCase4_get_nonexistent_application(tmp_path):

    setup_test_db(tmp_path)

    application = db_manager.get_application_status_by_request(
        999999
    )

    assert application is None


# Use Case 5

def test_UseCase5_cancel_application(tmp_path):
    setup_test_db(tmp_path)

    request_id = create_test_application()

    db_manager.update_application_status(
        request_id,
        "cancelled"
    )

    application = db_manager.get_application_status_by_request(
        request_id
    )

    assert application is not None
    assert application["status"] == "ΜΕ ΑΔΥΝΑΜΙΑ ΣΥΝΔΕΣΗΣ"
    assert application["termination_reason"] == "ΑΚΥΡΩΣΗ"
    assert application["date_cancelled"] is not None