# End-to-end tests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamlit.testing.v1 import AppTest


# Use Case 1

def test_UseCase1_off_topic_question():
    at = AppTest.from_file("../res_agent.py")
    at.run(timeout=30)

    at.chat_input[0].set_value(
        "Ποια είναι η πρωτεύουσα της Γαλλίας;"
    ).run(timeout=30)

    current_chat_id = at.session_state["current_chat_id"]
    messages = at.session_state["chats"][current_chat_id]["messages"]

    final_response = messages[-1]["content"].lower()

    assert messages

    assert "παρίσι" not in final_response
    assert (
        "απε" in final_response
        or "σηθυα" in final_response
        or "δεδδηε" in final_response
        or "αίτηση" in final_response
    )


# Use Case 2

def test_UseCase2_information_retrieval():
    at = AppTest.from_file("../res_agent.py")
    at.run(timeout=30)

    at.chat_input[0].set_value(
        "Ποια είναι τα δικαιολογητικά έγγραφα για νέα αίτηση σύνδεσης;"
    ).run(timeout=30)

    current_chat_id = at.session_state["current_chat_id"]
    messages = at.session_state["chats"][current_chat_id]["messages"]

    final_response = messages[-1]["content"].lower()

    assert messages
    assert final_response

    assert (
        "δικαιολογητικά" in final_response
        or "έγγραφα" in final_response
    )

    assert (
        "εγγυητική" in final_response
        or "βεβαίωση" in final_response
        or "τοπογραφικό" in final_response
        or "περιβαλλοντική" in final_response
        or "μονογραμμικό" in final_response
    )


# Use Case 3

def test_UseCase3_new_application_submission():
    at = AppTest.from_file("../res_agent.py")
    at.run(timeout=30)

    at.session_state["nav_selection"] = "📝 Πύλη Υποβολής"
    at.run(timeout=30)

    at.text_input[1].set_value("Δημήτριος")
    at.text_input[2].set_value("Αθανασάκης")
    at.text_input[3].set_value("139845620")
    at.text_input[4].set_value("Ηράκλειο")
    at.text_input[5].set_value("100")
    at.text_input[6].set_value("80")

    # Dropdowns
    at.selectbox[0].select("Φυσικό Πρόσωπο")

    at.selectbox[1].select(
        "Αυτοπαραγωγός Ταυτοχρονισμένου Συμψηφισμού με αποζημίωση ηλεκτρικής ενέργειας"
    )

    at.selectbox[2].select(
        "Φωτοβολταϊκός σταθμός (ΦΒ)"
    )

    at.run(timeout=30)

    at.selectbox[3].select(
        "Απευθείας συμμετοχή στην αγορά"
    )

    at.button[0].click()
    at.run(timeout=30)


# Use Case 4

def test_UseCase4_application_status():

    request_id = 30
    tax_id = "139845620"

    at = AppTest.from_file("../res_agent.py")
    at.run(timeout=30)

    at.chat_input[0].set_value(
        f"Θέλω να ελέγξω την κατάσταση της αίτησής μου. "
        f"Ο κωδικός αίτησης είναι {request_id} και ο ΑΦΜ μου είναι {tax_id}."
    ).run(timeout=30)

    import time
    time.sleep(2)

    current_chat_id = at.session_state["current_chat_id"]
    messages = at.session_state["chats"][current_chat_id]["messages"]

    final_response = messages[-1]["content"].lower()

    assert messages
    assert final_response

    assert "κωδικό αίτησης 30" in final_response
    assert "υποβολη αιτησης" in final_response


# Use Case 5

def test_UseCase5_application_cancellation():

    import db_manager

    request_id = 30
    tax_id = "139845620"

    db_manager.update_application_status(
        request_id,
        "non_binding"
    )

    at = AppTest.from_file("../res_agent.py")
    at.run(timeout=30)

    # Υποβολή ερωτήματος για τον έλεγχο της αίτησης
    at.chat_input[0].set_value(
        f"Θέλω να ακυρώσω την αίτησή μου. Ο κωδικός αίτησης είναι {request_id} και ο ΑΦΜ μου είναι {tax_id}."
    ).run(timeout=30)

    # Έλεγχος της τελικής κατάστασης στη βάση δεδομένων
    application = db_manager.get_application_status_by_request(
        request_id
    )

    assert application is not None
    assert application["status"] == "ΜΕ ΑΔΥΝΑΜΙΑ ΣΥΝΔΕΣΗΣ"
    assert application["termination_reason"] == "ΑΚΥΡΩΣΗ"

    assert application["date_cancelled"] is not None

    conn = db_manager.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET status = 'ΥΠΟΒΟΛΗ ΑΙΤΗΣΗΣ',
            termination_reason = NULL,
            date_non_binding = NULL,
            date_cancelled = NULL
        WHERE request_id = ?
    """, (request_id,))

    conn.commit()
    conn.close()