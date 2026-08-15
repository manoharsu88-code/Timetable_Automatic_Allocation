import sqlite3
import random
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)

app.secret_key = "my-secret-key-123"

DATABASE = "total.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def main():
    return render_template("login.html")


@app.route("/classrooms")
def classrooms():
    return render_template("classrooms.html")


@app.route("/timetable")
def timetable():
    return render_template("timetable.html")

@app.route("/lecturers")
def lecturers():

    return render_template("lecturers.html")

@app.route("/subjects")
def subject_page():

    return render_template(
        "subjects.html"
    )

@app.route("/lect")
def lect():

    return render_template("lect.html")

@app.route("/weekly-test")
def weekly_test_page():

    return render_template(
        "weekly_test.html"
    )

@app.route("/lecturer-section-allocation")
def lecturer_section_allocation_page():

    return render_template(
        "lecturer_sections.html"
    )

@app.route("/admin")
def admin_page():

    if session.get("role") != "admin":

        return redirect("/login")


    return render_template(
        "admin.html",
        username=session.get(
            "username"
        )
    )


@app.route(
    "/api/admin/users/<int:user_id>",
    methods=["DELETE"]
)
def admin_delete_user(user_id):

    # -----------------------------------------
    # ADMIN ONLY
    # -----------------------------------------

    if session.get("role") != "admin":

        return jsonify({

            "message":
                "Admin access required."

        }), 403


    # -----------------------------------------
    # PREVENT ADMIN FROM DELETING
    # THEMSELVES
    # -----------------------------------------

    if session.get("user_id") == user_id:

        return jsonify({

            "message":
                "You cannot delete your own "
                "admin account."

        }), 400


    conn = get_db()


    try:

        user = conn.execute("""
            SELECT id
            FROM users
            WHERE id = ?
        """, (
            user_id,
        )).fetchone()


        if user is None:

            return jsonify({

                "message":
                    "User not found."

            }), 404


        conn.execute("""
            DELETE FROM users
            WHERE id = ?
        """, (
            user_id,
        ))


        conn.commit()


        return jsonify({

            "message":
                "User deleted successfully."

        })


    except Exception as error:

        conn.rollback()

        print(
            "DELETE USER ERROR:",
            error
        )

        return jsonify({

            "message":
                "Unable to delete user."

        }), 500


    finally:

        conn.close()

@app.route(
    "/api/login",
    methods=["POST"]
)
def api_login():

    data = request.get_json()


    if not data:

        return jsonify({

            "message":
                "No login data received."

        }), 400


    username = str(
        data.get(
            "username",
            ""
        )
    ).strip()


    password = str(
        data.get(
            "password",
            ""
        )
    )


    role = str(
        data.get(
            "role",
            ""
        )
    ).strip().lower()


    if not username:

        return jsonify({

            "message":
                "Username is required."

        }), 400


    if not password:

        return jsonify({

            "message":
                "Password is required."

        }), 400


    if role not in (
        "admin",
        "lecturer",
        "student"
    ):

        return jsonify({

            "message":
                "Invalid login type."

        }), 400


    conn = get_db()


    try:

        user = conn.execute("""
            SELECT
                id,
                username,
                role
            FROM users
            WHERE username = ?
            AND password = ?
            AND role = ?
            LIMIT 1
        """, (
            username,
            password,
            role
        )).fetchone()


        if user is None:

            return jsonify({

                "message":
                    "Incorrect username, password, "
                    "or login type."

            }), 401


        # =========================================
        # STORE LOGIN SESSION
        # =========================================

        session["user_id"] = user["id"]

        session["username"] = user["username"]

        session["role"] = user["role"]


        # =========================================
        # REDIRECT
        # =========================================

        if role == "admin":

            redirect_url = "/admin"

        elif role == "lecturer":

            redirect_url = "/lecturer"

        else:

            redirect_url = "/student"


        return jsonify({

            "message":
                "Login successful.",

            "redirect":
                redirect_url

        })


    finally:

        conn.close()

@app.route("/lecturer")
def lecturer_page():

    if session.get("role") != "lecturer":

        return redirect("/login")


    return render_template(
        "mainpage.html",
        username=session.get(
            "username"
        )
    )

# =========================================================
# GET ALL LECTURER NAMES
# =========================================================

@app.route(
    "/api/lecturer-allocation/lecturers",
    methods=["GET"]
)
def get_all_allocation_lecturers():

    conn = get_db()

    try:

        rows = conn.execute("""
            SELECT DISTINCT name
            FROM lecturers
            WHERE name IS NOT NULL
            AND TRIM(name) != ''
            ORDER BY name
        """).fetchall()


        lecturers = [

            row["name"]

            for row in rows

        ]


        return jsonify({

            "lecturers":
                lecturers

        })


    finally:

        conn.close()

# =========================================================
# ALLOCATE SECTIONS TO LECTURERS
# =========================================================

@app.route(
    "/api/lecturer-allocation",
    methods=["POST"]
)
def allocate_lecturer_sections():

    data = request.get_json()


    if not data:

        return jsonify({

            "message":
                "No data received."

        }), 400


    lecturers =        data.get(
            "lecturers",
            []
        )


    if not isinstance(
        lecturers,
        list
    ):

        return jsonify({

            "message":
                "Invalid lecturer data."

        }), 400


    if not lecturers:

        return jsonify({

            "message":
                "No lecturers selected."

        }), 400


    conn = get_db()


    try:

        # =================================================
        # GET UNIQUE SECTIONS
        # =================================================

        rows = conn.execute("""
            SELECT DISTINCT class_name
            FROM timetable
            WHERE class_name IS NOT NULL
            AND TRIM(class_name) != ''
        """).fetchall()


        sections = [

            row["class_name"]

            for row in rows

        ]


        # =================================================
        # RANDOMIZE SECTIONS
        # =================================================

        import random

        random.shuffle(
            sections
        )


        # =================================================
        # CREATE SECTION SLOTS
        #
        # Every section can be used TWICE.
        #
        # Example:
        #
        # ECM -> 2 slots
        # ECE -> 2 slots
        # AIDS -> 2 slots
        #
        # Total = 6 lecturer allocations
        # =================================================

        section_slots = []


        for section in sections:

            section_slots.append(
                section
            )

            section_slots.append(
                section
            )


        # =================================================
        # RANDOMIZE SECTION SLOTS
        #
        # This makes the allocation random.
        # =================================================

        random.shuffle(
            section_slots
        )


        # =================================================
        # CREATE RESULT
        # =================================================

        allocations = []


        for lecturer in lecturers:

            section_name = None


            # ---------------------------------------------
            # TAKE ONE AVAILABLE SECTION
            # ---------------------------------------------

            if section_slots:

                section_name =     section_slots.pop()


            allocations.append({

                "lecturer_name":
                    lecturer,

                "section_name":
                    section_name

            })


        # =================================================
        # RETURN RESULT
        # =================================================

        return jsonify({

            "message":
                "Sections allocated successfully.",

            "allocations":
                allocations

        })


    except Exception as error:

        print(
            "LECTURER ALLOCATION ERROR:",
            error
        )


        return jsonify({

            "message":
                "Server error while allocating sections."

        }), 500


    finally:

        conn.close()


# =========================================================
# SAVE WEEKLY TEST
# =========================================================

@app.route(
    "/api/weekly-test",
    methods=["POST"]
)
def save_weekly_test():

    data = request.get_json()

    if not data:

        return jsonify({

            "message":
                "No data received."

        }), 400


    # =====================================================
    # GET DATA
    # =====================================================

    day = str(
        data.get(
            "day",
            ""
        )
    ).strip()


    try:

        from_period = int(
            data.get(
                "from_period"
            )
        )

        to_period = int(
            data.get(
                "to_period"
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "message":
                "Periods must be numbers."

        }), 400


    # =====================================================
    # VALID DAYS
    # =====================================================

    valid_days = [

        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"

    ]


    # Make comparison case-insensitive

    matched_day = None

    for valid_day in valid_days:

        if valid_day.lower() == day.lower():

            matched_day = valid_day

            break


    if matched_day is None:

        return jsonify({

            "message":
                "Invalid day. Only Monday to Saturday are allowed."

        }), 400


    # =====================================================
    # VALIDATE PERIODS
    # =====================================================

    if (
        from_period < 1
        or from_period > 7
    ):

        return jsonify({

            "message":
                "From period must be between 1 and 7."

        }), 400


    if (
        to_period < 1
        or to_period > 7
    ):

        return jsonify({

            "message":
                "To period must be between 1 and 7."

        }), 400


    if from_period > to_period:

        return jsonify({

            "message":
                "From period must be less than or equal to To period."

        }), 400


    conn = get_db()


    try:

        # =================================================
        # UPDATE ALL SECTIONS
        #
        # Only timetable rows belonging to the selected
        # day and selected period range are changed.
        # =================================================

        cursor = conn.execute("""
            UPDATE timetable

            SET subject = ?,
                room_name = NULL

            WHERE day = ?

            AND period_no >= ?

            AND period_no <= ?
        """, (
            "Weekly Test",
            matched_day,
            from_period,
            to_period
        ))


        updated_rows = cursor.rowcount


        # =================================================
        # COMMIT
        # =================================================

        conn.commit()


        return jsonify({

            "message":
                "Weekly Test saved successfully for all sections.",

            "day":
                matched_day,

            "from_period":
                from_period,

            "to_period":
                to_period,

            "updated_rows":
                updated_rows

        }), 200


    except Exception as error:

        conn.rollback()

        print(
            "WEEKLY TEST ERROR:",
            error
        )

        return jsonify({

            "message":
                "Server error while updating timetable."

        }), 500


    finally:

        conn.close()


# =========================================================
# SUBJECT 3-PERIOD BLOCK PAGE
# =========================================================

@app.route("/subjects_lab")
def subjects_three_page():

    return render_template(
        "subjects_lab.html"
    )


# =========================================================
# GET SUGGESTIONS FOR SUBJECT-3 PAGE
# =========================================================

@app.route(
    "/api/subjects3/suggestions",
    methods=["GET"]
)
def subjects3_suggestions():

    conn = get_db()

    try:

        # ---------------------------------------------
        # SUBJECTS FROM LECTURERS
        # ---------------------------------------------

        subject_rows = conn.execute("""
            SELECT DISTINCT subject
            FROM lecturers
            WHERE subject IS NOT NULL
            AND TRIM(subject) != ''
            ORDER BY subject
        """).fetchall()


        # ---------------------------------------------
        # SECTIONS FROM TIMETABLE
        # ---------------------------------------------

        section_rows = conn.execute("""
            SELECT DISTINCT class_name
            FROM timetable
            WHERE class_name IS NOT NULL
            AND TRIM(class_name) != ''
            ORDER BY class_name
        """).fetchall()


        return jsonify({

            "subjects": [
                row["subject"]
                for row in subject_rows
            ],

            "sections": [
                row["class_name"]
                for row in section_rows
            ]

        })


    finally:

        conn.close()


# =========================================================
# GET SUBJECT3 TABLE
# =========================================================

@app.route(
    "/api/subjects3",
    methods=["GET"]
)
def get_subjects3():

    conn = get_db()

    try:

        rows = conn.execute("""
            SELECT
                id,
                subject,
                section_name,
                lab
            FROM subjects
            ORDER BY id
        """).fetchall()


        return jsonify([
            dict(row)
            for row in rows
        ])

    finally:

        conn.close()


# =========================================================
# DAY NUMBERS
# =========================================================

DAY_NAMES = {

    1: "Monday",

    2: "Tuesday",

    3: "Wednesday",

    4: "Thursday",

    5: "Friday",

    6: "Saturday"

}


DAY_NUMBERS = {

    "Monday": 1,

    "Tuesday": 2,

    "Wednesday": 3,

    "Thursday": 4,

    "Friday": 5,

    "Saturday": 6

}


# =========================================================
# LAB -> TWO DIGIT LOCATIONS
#
# Example:
#
# 6351
#
# becomes:
#
# [63, 51]
# =========================================================

def lab_to_locations(lab):

    locations = []

    if lab is None:

        return locations


    text = str(lab).strip()


    if not text:

        return locations


    # LAB must contain an even number
    # of digits

    if len(text) % 2 != 0:

        return locations


    for i in range(
        0,
        len(text),
        2
    ):

        try:

            number = int(
                text[i:i + 2]
            )

            locations.append(number)

        except ValueError:

            pass


    return locations


# =========================================================
# GET LECTURER FOR SUBJECT
# =========================================================

def get_lecturer_for_subject(
    conn,
    subject
):

    row = conn.execute("""
        SELECT
            name,
            total_periods
        FROM lecturers
        WHERE LOWER(TRIM(subject))
              = LOWER(TRIM(?))
        ORDER BY id
        LIMIT 1
    """, (
        subject,
    )).fetchone()


    return row


# =========================================================
# GET ALL LAB LOCATIONS OF SUBJECTS BELONGING
# TO THE SAME LECTURER
#
# IMPORTANT:
#
# If lecturer = Anil
#
# BEEE       -> labs
# BEEE-Lab   -> labs
#
# all are collected.
# =========================================================

def get_lecturer_kim(
    conn,
    lecturer_name
):

    rows = conn.execute("""
        SELECT
            subject,
            section_name,
            lab
        FROM subjects
        WHERE EXISTS (

            SELECT 1

            FROM lecturers l

            WHERE LOWER(TRIM(l.name))
                  = LOWER(TRIM(?))

            AND LOWER(TRIM(l.subject))
                  = LOWER(TRIM(subject))

        )
    """, (
        lecturer_name,
    )).fetchall()


    kim = []


    for row in rows:

        lab = row["lab"]


        for location in lab_to_locations(
            lab
        ):

            kim.append(location)


    return kim


# =========================================================
# GET CURRENT SUBJECT LOCATIONS
# =========================================================

def get_current_subject_locations(
    conn,
    section,
    subject
):

    rows = conn.execute("""
        SELECT
            day,
            period_no
        FROM timetable
        WHERE LOWER(TRIM(class_name))
              = LOWER(TRIM(?))

        AND LOWER(TRIM(subject))
              = LOWER(TRIM(?))

        ORDER BY
            day,
            period_no
    """, (
        section,
        subject
    )).fetchall()


    locations = []


    for row in rows:

        day = row["day"]

        period = int(
            row["period_no"]
        )


        day_no = DAY_NUMBERS.get(
            day
        )


        if day_no is None:

            continue


        locations.append(
            day_no * 10 + period
        )


    return locations


# =========================================================
# CHECK IF SECTION LOCATION IS EMPTY
# =========================================================

def section_slot_is_empty(
    conn,
    section,
    day,
    period
):

    row = conn.execute("""
        SELECT subject
        FROM timetable
        WHERE LOWER(TRIM(class_name))
              = LOWER(TRIM(?))

        AND day = ?

        AND period_no = ?

        LIMIT 1
    """, (
        section,
        day,
        period
    )).fetchone()


    # No timetable row means it cannot
    # be used.

    if row is None:

        return False


    # NULL means empty

    return row["subject"] is None


# =========================================================
# CHECK THREE CONSECUTIVE LOCATIONS
#
# Example:
#
# 34
#
# checks:
#
# 34
# 35
# 36
#
# Both conditions must be satisfied:
#
# 1. Section slots are empty
# 2. None of the locations exist in KIM
# =========================================================

def block_is_available(
    conn,
    section,
    day_number,
    start_period,
    total_periods,
    kim
):

    # -------------------------------------------------
    # CHECK THAT THE BLOCK FITS INSIDE PERIOD 1-7
    # -------------------------------------------------

    if start_period < 1:
        return False

    if start_period + total_periods - 1 > 7:
        return False


    day = DAY_NAMES[day_number]


    # -------------------------------------------------
    # CHECK EVERY PERIOD IN THE BLOCK
    # -------------------------------------------------

    for offset in range(total_periods):

        period = start_period + offset

        location = (
            day_number * 10
            + period
        )


        # ---------------------------------------------
        # CHECK SECTION TIMETABLE
        # ---------------------------------------------

        if not section_slot_is_empty(
            conn,
            section,
            day,
            period
        ):

            return False


        # ---------------------------------------------
        # CHECK KIM
        # ---------------------------------------------

        if location in kim:

            return False


    return True

# =========================================================
# FIND THREE-PERIOD LOCATION
#
# RANDOM:
#
# 5 attempts
#
# SYSTEMATIC:
#
# 11
# 12
# 13
# 14
# 15
# 21
# ...
# 55
#
# We do NOT use 16/17 because three periods
# would go outside the day.
# =========================================================

def find_block_location(
    conn,
    section,
    kim,
    total_periods
):

    import random


    # -------------------------------------------------
    # MAXIMUM POSSIBLE START PERIOD
    #
    # Example:
    #
    # total_periods = 3
    # maximum start = 5
    #
    # total_periods = 5
    # maximum start = 3
    #
    # total_periods = 7
    # maximum start = 1
    # -------------------------------------------------

    max_start_period = (
        7 - total_periods + 1
    )


    if max_start_period < 1:

        return None


    # -------------------------------------------------
    # RANDOM 5 ATTEMPTS
    # -------------------------------------------------

    tried = set()


    for _ in range(5):

        day_number = random.randint(
            1,
            6
        )


        start_period = random.randint(
            1,
            max_start_period
        )


        key = (
            day_number,
            start_period
        )


        if key in tried:

            continue


        tried.add(key)


        if block_is_available(
            conn,
            section,
            day_number,
            start_period,
            total_periods,
            kim
        ):

            return (
                day_number,
                start_period
            )


    # -------------------------------------------------
    # SYSTEMATIC SEARCH
    # -------------------------------------------------

    for day_number in range(
        1,
        7
    ):

        for start_period in range(
            1,
            max_start_period + 1
        ):

            key = (
                day_number,
                start_period
            )


            if key in tried:

                continue


            if block_is_available(
                conn,
                section,
                day_number,
                start_period,
                total_periods,
                kim
            ):

                return (
                    day_number,
                    start_period
                )


    # -------------------------------------------------
    # NOTHING FOUND
    # -------------------------------------------------

    return None

def assign_three_period_block(
    conn,
    subject,
    section,
    total_periods,
    kim
):

    # -------------------------------------------------
    # CURRENT SUBJECT PERIODS
    # -------------------------------------------------

    current_locations = get_current_subject_locations(
        conn,
        section,
        subject
    )

    current_count = len(current_locations)


    # -------------------------------------------------
    # TOO MANY
    # -------------------------------------------------

    if current_count > total_periods:

        raise ValueError(
            "Timetable is filled incorrectly. "
            "The subject '" + subject +
            "' already appears " +
            str(current_count) +
            " times in " + section +
            ", but total periods is " +
            str(total_periods) +
            ". Please check the timetable."
        )


    # -------------------------------------------------
    # ALREADY COMPLETE
    # -------------------------------------------------

    if current_count == total_periods:

        return []


    # -------------------------------------------------
    # REMAINING PERIODS
    # -------------------------------------------------

    required = (
        total_periods -
        current_count
    )


    # -------------------------------------------------
    # IMPORTANT
    #
    # If there are already some occurrences,
    # don't create another full X-period block.
    #
    # A full block is only possible when
    # current_count == 0.
    # -------------------------------------------------

    if current_count != 0:

        raise ValueError(
            "The subject already has " +
            str(current_count) +
            " period(s) in this section. "
            "The remaining periods cannot form "
            "a complete consecutive block."
        )


    # -------------------------------------------------
    # FIND X-PERIOD BLOCK
    # -------------------------------------------------

    location = find_block_location(
        conn,
        section,
        kim,
        total_periods
    )


    if location is None:

        raise ValueError(
            "Unable to find a valid " +
            str(total_periods) +
            "-period block for subject '" +
            subject +
            "' in section '" +
            section +
            "'. Please check the timetable."
        )


    day_number, start_period = location


    day = DAY_NAMES[
        day_number
    ]


    added_locations = []


    # -------------------------------------------------
    # PLACE SUBJECT IN ALL X PERIODS
    # -------------------------------------------------

    for offset in range(
        total_periods
    ):

        period = (
            start_period +
            offset
        )


        if period > 7:

            raise ValueError(
                "Invalid timetable block."
            )


        # ---------------------------------------------
        # UPDATE TIMETABLE
        # ---------------------------------------------

        cursor = conn.execute("""
            UPDATE timetable

            SET
                subject = ?,
                room_name = NULL

            WHERE
                LOWER(TRIM(class_name))
                = LOWER(TRIM(?))

            AND day = ?

            AND period_no = ?

            AND subject IS NULL

        """, (
            subject,
            section,
            day,
            period
        ))


        if cursor.rowcount == 0:

            raise ValueError(
                "Unable to update timetable at "
                + day +
                " period " +
                str(period)
            )


        # ---------------------------------------------
        # CREATE LOCATION
        # ---------------------------------------------

        location_number = (
            day_number * 10
            + period
        )


        added_locations.append(
            location_number
        )


    # -------------------------------------------------
    # RETURN LOCATIONS
    # -------------------------------------------------

    return added_locations


# =========================================================
# SAVE SUBJECT - THREE PERIOD VERSION
# =========================================================

@app.route(
    "/api/subjects3",
    methods=["POST"]
)
def add_subject3():

    data =        request.get_json()


    if not data:

        return jsonify({

            "message":
                "No data received."

        }), 400


    subject =      str(
            data.get(
                "subject",
                ""
            )
        ).strip()


    section =      str(
            data.get(
                "section_name",
                ""
            )
        ).strip()


    if not subject:

        return jsonify({

            "message":
                "Subject is required."

        }), 400


    if not section:

        return jsonify({

            "message":
                "Section is required."

        }), 400


    conn = get_db()


    try:

        # =============================================
        # FIND LECTURER
        # =============================================

        lecturer =          get_lecturer_for_subject(
                conn,
                subject
            )


        if lecturer is None:

            return jsonify({

                "message":
                    "Subject does not exist "
                    "in lecturers database."

            }), 400


        lecturer_name =            lecturer["name"]


        total_periods =            int(
                lecturer["total_periods"]
            )


        # =============================================
        # CHECK SECTION
        # =============================================

        section_row =            conn.execute("""
                SELECT id
                FROM timetable
                WHERE LOWER(TRIM(class_name))
                      = LOWER(TRIM(?))
                LIMIT 1
            """, (
                section,
            )).fetchone()


        if section_row is None:

            return jsonify({

                "message":
                    "Section does not exist "
                    "in timetable database."

            }), 400


        # =============================================
        # DUPLICATE SUBJECT + SECTION
        # =============================================

        duplicate =            conn.execute("""
                SELECT id
                FROM subjects
                WHERE LOWER(TRIM(subject))
                      = LOWER(TRIM(?))

                AND LOWER(TRIM(section_name))
                      = LOWER(TRIM(?))

                LIMIT 1
            """, (
                subject,
                section
            )).fetchone()


        if duplicate:

            return jsonify({

                "message":
                    "This subject is already "
                    "created for this section."

            }), 400


        # =============================================
        # KIM
        #
        # All LAB locations belonging to the
        # same lecturer.
        # =============================================

        kim =            get_lecturer_kim(
                conn,
                lecturer_name
            )


        # =============================================
        # INSERT SUBJECT FIRST
        # =============================================

        cursor =            conn.execute("""
                INSERT INTO subjects
                (
                    subject,
                    section_name,
                    lab
                )
                VALUES (?, ?, ?)
            """, (
                subject,
                section,
                0
            ))


        subject_id =            cursor.lastrowid


        # =============================================
        # ASSIGN SUBJECT
        # =============================================

        added =            assign_three_period_block(
                conn,
                subject,
                section,
                total_periods,
                kim
            )


        # =============================================
        # GET FINAL LOCATIONS
        # =============================================

        final_locations =            get_current_subject_locations(
                conn,
                section,
                subject
            )


        # =============================================
        # CREATE LAB
        #
        # Example:
        #
        # [34, 51]
        #
        # becomes:
        #
        # 3451
        # =============================================

        # =============================================
# CREATE LAB VALUE
# =============================================

        lab_string = "".join(
            str(location)
            for location in final_locations
        )

        if lab_string:
            lab_value = int(lab_string)
        else:
            lab_value = 0
        # =============================================
        # UPDATE LAB
        # =============================================

        conn.execute("""
            UPDATE subjects
            SET lab = ?
            WHERE id = ?
        """, (
            lab_value,
            subject_id
        ))


        conn.commit()


        return jsonify({

            "message":
                "Subject saved and timetable "
                "updated successfully.",

            "id":
                subject_id,

            "subject":
                subject,

            "section_name":
                section,

            "lecturer":
                lecturer_name,

            "total_periods":
                total_periods,

            "lab":
                lab_value,

            "added":
                len(added)

        }), 201


    except ValueError as error:

        conn.rollback()

        return jsonify({

            "message":
                str(error)

        }), 400


    except Exception as error:

        conn.rollback()

        print(
            "SUBJECT3 ERROR:",
            error
        )

        return jsonify({

            "message":
                "Server error while processing subject."

        }), 500


    finally:

        conn.close()


# =========================================================
# UPDATE LAB - THREE PERIOD VERSION
# =========================================================

@app.route(
    "/api/subjects3/<int:subject_id>",
    methods=["PUT"]
)
def update_subject3(subject_id):

    data =        request.get_json()


    if not data:

        return jsonify({

            "message":
                "No data received."

        }), 400


    if data.get(
        "update_lab"
    ) is not True:

        return jsonify({

            "message":
                "Only LAB update is allowed."

        }), 400


    conn = get_db()


    try:

        # =============================================
        # GET SUBJECT
        # =============================================

        record =            conn.execute("""
                SELECT
                    subject,
                    section_name
                FROM subjects
                WHERE id = ?
            """, (
                subject_id,
            )).fetchone()


        if record is None:

            return jsonify({

                "message":
                    "Subject record not found."

            }), 404


        subject =            record["subject"]


        section =            record["section_name"]


        # =============================================
        # GET LECTURER
        # =============================================

        lecturer =            get_lecturer_for_subject(
                conn,
                subject
            )


        if lecturer is None:

            return jsonify({

                "message":
                    "Lecturer for this subject "
                    "was not found."

            }), 400


        lecturer_name =            lecturer["name"]


        # =============================================
        # GET KIM
        #
        # IMPORTANT:
        #
        # Remove this record's CURRENT LAB
        # from the conflict list.
        #
        # Otherwise the subject would conflict
        # with its own old locations.
        # =============================================

        kim = []


        rows = conn.execute("""
            SELECT
                id,
                lab
            FROM subjects
            WHERE id != ?
        """, (
            subject_id,
        )).fetchall()


        for row in rows:

            # Check whether this subject belongs
            # to the same lecturer.

            owner = conn.execute("""
                SELECT id
                FROM lecturers
                WHERE LOWER(TRIM(name))
                      = LOWER(TRIM(?))

                AND LOWER(TRIM(subject))
                      = LOWER(TRIM(
                          (
                              SELECT subject
                              FROM subjects
                              WHERE id = ?
                          )
                      ))

                LIMIT 1
            """, (
                lecturer_name,
                row["id"]
            )).fetchone()


            # The above query is intentionally not
            # used for the final filtering below.
            # We use a simpler query instead.

        # =============================================
        # GET ALL SUBJECT NAMES OF LECTURER
        # =============================================

        lecturer_subject_rows =            conn.execute("""
                SELECT DISTINCT subject
                FROM lecturers
                WHERE LOWER(TRIM(name))
                      = LOWER(TRIM(?))
            """, (
                lecturer_name,
            )).fetchall()


        lecturer_subjects = [

            row["subject"]

            for row
            in lecturer_subject_rows

        ]


        # =============================================
        # GET LABS FOR THOSE SUBJECTS
        # EXCLUDING CURRENT SUBJECT RECORD
        # =============================================

        if lecturer_subjects:

            placeholders =                ",".join(
                    ["?"]
                    * len(lecturer_subjects)
                )


            params =                lecturer_subjects.copy()


            params.append(
                subject_id
            )


            lab_rows =                conn.execute(
                    f"""
                    SELECT lab
                    FROM subjects
                    WHERE LOWER(TRIM(subject))
                    IN (
                        {placeholders}
                    )

                    AND id != ?
                    """,
                    params
                ).fetchall()


            for row in lab_rows:

                for location in lab_to_locations(
                    row["lab"]
                ):

                    kim.append(
                        location
                    )


        # =============================================
        # CURRENT SUBJECT LOCATIONS
        # =============================================

        current_locations =            get_current_subject_locations(
                conn,
                section,
                subject
            )


        # =============================================
        # CHECK EACH CURRENT LOCATION
        #
        # For UPDATE:
        #
        # 34 -> checks 34,35,36
        #
        # 55 -> checks 55,56,57
        #
        # =============================================

        for location in current_locations:

            day_number =                location // 10


            period =                location % 10


            # Only valid 3-block starts

            if (
                day_number < 1
                or day_number > 6
                or period < 1
                or period > 5
            ):

                return jsonify({

                    "message":
                        "Manual update error: "
                        "invalid three-period "
                        "location " +
                        str(location) +
                        " found in LAB."

                }), 409


            block = [

                location,

                location + 1,

                location + 2

            ]


            for value in block:

                if value in kim:

                    return jsonify({

                        "message":
                            "Manual update error: "
                            "location " +
                            str(value) +
                            " conflicts with "
                            "another subject taught "
                            "by lecturer " +
                            lecturer_name +
                            "."

                    }), 409


        # =============================================
        # BUILD NEW LAB
        # =============================================

        lab_string =            "".join(
                str(location)
                for location
                in current_locations
            )

        if lab_string:
            lab_value = int(lab_string)
        else:
            lab_value = 0

        # =============================================
        # UPDATE
        # =============================================

        conn.execute("""
            UPDATE subjects
            SET lab = ?
            WHERE id = ?
        """, (
            lab_value,
            subject_id
        ))


        conn.commit()


        return jsonify({

            "message":
                "LAB updated successfully.",

            "id":
                subject_id,

            "subject":
                subject,

            "section_name":
                section,

            "lab":
                lab_value

        }), 200


    except Exception as error:

        conn.rollback()

        print(
            "SUBJECT3 UPDATE ERROR:",
            error
        )

        return jsonify({

            "message":
                "Unable to update LAB."

        }), 500


    finally:

        conn.close()


# =========================================================
# DELETE SUBJECT - THREE PAGE
# =========================================================

@app.route(
    "/api/subjects3/<int:subject_id>",
    methods=["DELETE"]
)
def delete_subject3(subject_id):

    conn = get_db()


    try:

        # =============================================
        # GET SUBJECT
        # =============================================

        row =            conn.execute("""
                SELECT
                    subject,
                    section_name
                FROM subjects
                WHERE id = ?
            """, (
                subject_id,
            )).fetchone()


        if row is None:

            return jsonify({

                "message":
                    "Subject record not found."

            }), 404


        subject =            row["subject"]


        section =            row["section_name"]


        # =============================================
        # CLEAR TIMETABLE
        # =============================================

        conn.execute("""
            UPDATE timetable
            SET
                subject = NULL,
                room_name = NULL

            WHERE LOWER(TRIM(class_name))
                  = LOWER(TRIM(?))

            AND LOWER(TRIM(subject))
                  = LOWER(TRIM(?))
        """, (
            section,
            subject
        ))


        # =============================================
        # DELETE SUBJECT
        # =============================================

        conn.execute("""
            DELETE FROM subjects
            WHERE id = ?
        """, (
            subject_id,
        ))


        conn.commit()


        return jsonify({

            "message":
                "Subject deleted and its timetable "
                "entries were cleared."

        }), 200


    except Exception as error:

        conn.rollback()

        print(
            "SUBJECT3 DELETE ERROR:",
            error
        )

        return jsonify({

            "message":
                "Unable to delete subject."

        }), 500


    finally:

        conn.close()

# =========================================================
# DAY NUMBERS
# =========================================================

DAY_NUMBERS = {

    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6

}


DAYS = [

    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"

]


# =========================================================
# COMBINATION
# =========================================================

def make_combination(day, period):

    day_no = DAY_NUMBERS.get(day)

    if day_no is None:
        return None

    return int(str(day_no) + str(period))


# =========================================================
# SPLIT LAB INTO TWO-DIGIT COMBINATIONS
# =========================================================
#
# Example:
#
# 6351
#
# becomes:
#
# [63, 51]
#
# 336789
#
# becomes:
#
# [33, 67, 89]
#
# =========================================================

def split_lab(lab):

    if lab is None:
        return []

    text = str(lab).strip()

    if not text:
        return []

    # Remove negative sign if accidentally present
    if text.startswith("-"):
        text = text[1:]

    result = []

    # Only complete pairs
    for i in range(0, len(text) - 1, 2):

        pair = text[i:i + 2]

        try:

            result.append(
                int(pair)
            )

        except ValueError:

            pass

    return result


# =========================================================
# GET LECTURER INFORMATION FOR SUBJECT
# =========================================================

def get_lecturer_for_subject(conn, subject):

    row = conn.execute("""
        SELECT
            name,
            total_periods
        FROM lecturers
        WHERE LOWER(TRIM(subject))
              = LOWER(TRIM(?))
        ORDER BY id
        LIMIT 1
    """, (
        subject,
    )).fetchone()

    return row


# =========================================================
# GET ALL SUBJECTS OF SAME LECTURER
# =========================================================

def get_lecturer_subjects(conn, lecturer_name):

    rows = conn.execute("""
        SELECT DISTINCT subject
        FROM lecturers
        WHERE LOWER(TRIM(name))
              = LOWER(TRIM(?))
        AND subject IS NOT NULL
        AND TRIM(subject) != ''
        ORDER BY subject
    """, (
        lecturer_name,
    )).fetchall()

    return [
        row["subject"]
        for row in rows
    ]


# =========================================================
# GET KIM ARRAY
# =========================================================
#
# For a lecturer:
#
#   Get all subjects taught by lecturer
#
#   Then get all LAB values belonging to those
#   subjects from subjects table.
#
# Example:
#
# BEEE     -> 1165434723
# BEEE-Lab -> 434727
#
# kim becomes:
#
# [
#     1165434723,
#     434727
# ]
#
# =========================================================

def get_kim_array(
    conn,
    lecturer_name,
    exclude_subject=None,
    exclude_id=None
):

    subjects = get_lecturer_subjects(
        conn,
        lecturer_name
    )

    if not subjects:

        return []


    kim = []


    for subject in subjects:

        rows = conn.execute("""
            SELECT id, lab
            FROM subjects
            WHERE LOWER(TRIM(subject))
                  = LOWER(TRIM(?))
        """, (
            subject,
        )).fetchall()


        for row in rows:

            # Exclude current subject record during update
            if exclude_id is not None:

                if row["id"] == exclude_id:
                    continue


            # Optional subject exclusion
            if exclude_subject is not None:

                if (
                    row["subject"].strip().lower()
                    ==
                    exclude_subject.strip().lower()
                ):
                    continue


            lab = row["lab"]

            if lab is None:
                continue

            if str(lab).strip() == "":
                continue

            try:

                lab_number = int(lab)

            except ValueError:

                continue


            if lab_number == 0:
                continue


            kim.append(lab_number)


    return kim


# =========================================================
# CREATE KIM PAIR SET
# =========================================================
#
# Instead of repeatedly searching:
#
# [336789, 564334]
#
# becomes:
#
# {33, 67, 89, 56, 43, 34}
#
# =========================================================

def get_kim_pairs(kim):

    pairs = set()


    for lab in kim:

        for pair in split_lab(lab):

            pairs.add(pair)


    return pairs


# =========================================================
# CHECK COMBINATION AGAINST KIM
# =========================================================

def combination_exists_in_kim(
    combination,
    kim_pairs
):

    return combination in kim_pairs


# =========================================================
# GET SUBJECT OCCURRENCES IN SECTION
# =========================================================

def get_subject_occurrences(
    conn,
    section,
    subject
):

    rows = conn.execute("""
        SELECT
            day,
            period_no
        FROM timetable
        WHERE LOWER(TRIM(class_name))
              = LOWER(TRIM(?))
        AND LOWER(TRIM(subject))
              = LOWER(TRIM(?))
        ORDER BY
            CASE day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                ELSE 7
            END,
            period_no
    """, (
        section,
        subject
    )).fetchall()


    combinations = []


    for row in rows:

        combination = make_combination(
            row["day"],
            int(row["period_no"])
        )


        if combination is not None:

            combinations.append(
                combination
            )


    return combinations


# =========================================================
# CREATE LAB FROM OCCURRENCES
# =========================================================
#
# [63, 51]
#
# becomes:
#
# 6351
#
# =========================================================

def make_lab_from_occurrences(
    combinations
):

    return "".join(
        str(number)
        for number in combinations
    )


# =========================================================
# CHECK SECTION LOCATION
# =========================================================

def section_location_is_empty(
    conn,
    section,
    day,
    period
):

    row = conn.execute("""
        SELECT subject
        FROM timetable
        WHERE LOWER(TRIM(class_name))
              = LOWER(TRIM(?))
        AND day = ?
        AND period_no = ?
        LIMIT 1
    """, (
        section,
        day,
        period
    )).fetchone()


    # Location does not exist
    if row is None:

        return False


    # NULL means empty
    return row["subject"] is None


# =========================================================
# FIND LOCATION
# =========================================================

def find_location(
    conn,
    section,
    subject,
    kim_pairs
):

    tried = set()


    # =====================================================
    # FIRST TRY 5 RANDOM LOCATIONS
    # =====================================================

    for _ in range(5):

        day = random.choice(DAYS)

        period = random.randint(
            1,
            7
        )


        key = (
            day,
            period
        )


        if key in tried:

            continue


        tried.add(key)


        combination = make_combination(
            day,
            period
        )


        # -------------------------------------------------
        # CONDITION 1:
        # SECTION LOCATION MUST BE EMPTY
        # -------------------------------------------------

        if not section_location_is_empty(
            conn,
            section,
            day,
            period
        ):

            continue


        # -------------------------------------------------
        # CONDITION 2:
        # COMBINATION MUST NOT EXIST IN KIM
        # -------------------------------------------------

        if combination_exists_in_kim(
            combination,
            kim_pairs
        ):

            continue


        return (
            day,
            period
        )


    # =====================================================
    # SYSTEMATIC SEARCH
    #
    # 11
    # 12
    # ...
    # 17
    #
    # 21
    # 22
    # ...
    #
    # 61
    # ...
    # 67
    # =====================================================

    for day_number in range(1, 7):

        day = DAYS[
            day_number - 1
        ]


        for period in range(1, 8):

            key = (
                day,
                period
            )


            if key in tried:

                continue


            combination = (
                day_number * 10
                + period
            )


            # ------------------------------------------------
            # SECTION MUST BE EMPTY
            # ------------------------------------------------

            if not section_location_is_empty(
                conn,
                section,
                day,
                period
            ):

                continue


            # ------------------------------------------------
            # KIM CONFLICT
            # ------------------------------------------------

            if combination_exists_in_kim(
                combination,
                kim_pairs
            ):

                continue


            return (
                day,
                period
            )


    return None


# =========================================================
# GET SUBJECT PERIOD COUNT
# =========================================================

def get_total_periods(
    conn,
    subject
):

    row = conn.execute("""
        SELECT total_periods
        FROM lecturers
        WHERE LOWER(TRIM(subject))
              = LOWER(TRIM(?))
        ORDER BY id
        LIMIT 1
    """, (
        subject,
    )).fetchone()


    if row is None:

        return None


    return int(
        row["total_periods"]
    )


# =========================================================
# ASSIGN SUBJECT TO TIMETABLE
# =========================================================

def assign_subject(
    conn,
    subject,
    section,
    kim_pairs
):

    total_periods = get_total_periods(
        conn,
        subject
    )


    if total_periods is None:

        raise ValueError(
            "Subject does not exist in "
            "lecturers database."
        )


    # =====================================================
    # CURRENT OCCURRENCES
    # =====================================================

    occurrences = get_subject_occurrences(
        conn,
        section,
        subject
    )


    current_count = len(
        occurrences
    )


    # =====================================================
    # TOO MANY
    # =====================================================

    if current_count > total_periods:

        raise ValueError(
            "Timetable is filled incorrectly. "
            "The subject '" +
            subject +
            "' appears " +
            str(current_count) +
            " times in section '" +
            section +
            "', but total periods is " +
            str(total_periods) +
            ". Please check the timetable."
        )


    # =====================================================
    # ALREADY COMPLETE
    # =====================================================

    if current_count == total_periods:

        return {
            "added": 0,
            "total": total_periods,
            "occurrences":
                occurrences
        }


    required = (
        total_periods
        - current_count
    )


    added = 0


    # =====================================================
    # ADD REQUIRED PERIODS
    # =====================================================

    for _ in range(required):

        location = find_location(
            conn,
            section,
            subject,
            kim_pairs
        )


        if location is None:

            raise ValueError(
                "Unable to find a valid timetable "
                "location for subject '" +
                subject +
                "' in section '" +
                section +
                "'. All possible locations "
                "are occupied or conflict with "
                "another subject of the same lecturer."
            )


        day, period = location


        # =================================================
        # UPDATE NULL LOCATION
        # =================================================

        cursor = conn.execute("""
            UPDATE timetable
            SET
                subject = ?,
                room_name = NULL
            WHERE LOWER(TRIM(class_name))
                  = LOWER(TRIM(?))
            AND day = ?
            AND period_no = ?
            AND subject IS NULL
        """, (
            subject,
            section,
            day,
            period
        ))


        if cursor.rowcount == 0:

            raise ValueError(
                "Unable to update selected "
                "timetable location."
            )


        added += 1


        # =================================================
        # IMPORTANT:
        #
        # New location must also be added to KIM so that
        # another period assigned during this same
        # operation cannot use the same combination.
        # =================================================

        combination = make_combination(
            day,
            period
        )


        kim_pairs.add(
            combination
        )


    occurrences = get_subject_occurrences(
        conn,
        section,
        subject
    )


    return {

        "added": added,

        "total": total_periods,

        "occurrences":
            occurrences

    }


# =========================================================
# GET SUBJECT + SECTION SUGGESTIONS
# =========================================================

@app.route(
    "/api/subjects/suggestions",
    methods=["GET"]
)
def subject_suggestions():

    conn = get_db()


    try:

        # =================================================
        # SUBJECTS FROM LECTURERS
        # =================================================

        subject_rows = conn.execute("""
            SELECT DISTINCT subject
            FROM lecturers
            WHERE subject IS NOT NULL
            AND TRIM(subject) != ''
            ORDER BY subject
        """).fetchall()


        # =================================================
        # SECTIONS FROM TIMETABLE
        # =================================================

        section_rows = conn.execute("""
            SELECT DISTINCT class_name
            FROM timetable
            WHERE class_name IS NOT NULL
            AND TRIM(class_name) != ''
            ORDER BY class_name
        """).fetchall()


        return jsonify({

            "subjects": [
                row["subject"]
                for row in subject_rows
            ],

            "sections": [
                row["class_name"]
                for row in section_rows
            ]

        })


    finally:

        conn.close()


# =========================================================
# GET ALL CREATED SUBJECTS
# =========================================================

@app.route(
    "/api/subjects",
    methods=["GET"]
)
def get_subjects():

    conn = get_db()


    try:

        rows = conn.execute("""
            SELECT
                id,
                subject,
                section_name,
                lab
            FROM subjects
            ORDER BY id
        """).fetchall()


        return jsonify([
            dict(row)
            for row in rows
        ])


    finally:

        conn.close()


# =========================================================
# CREATE SUBJECT
# =========================================================

@app.route(
    "/api/subjects",
    methods=["POST"]
)
def add_subject():

    data = request.get_json()


    if not data:

        return jsonify({
            "message":
                "No data received."
        }), 400


    subject = str(
        data.get(
            "subject",
            ""
        )
    ).strip()


    section = str(
        data.get(
            "section_name",
            ""
        )
    ).strip()


    if not subject:

        return jsonify({
            "message":
                "Please enter a subject."
        }), 400


    if not section:

        return jsonify({
            "message":
                "Please enter a section."
        }), 400


    conn = get_db()


    try:

        # =================================================
        # CHECK SUBJECT
        # =================================================

        lecturer = get_lecturer_for_subject(
            conn,
            subject
        )


        if lecturer is None:

            return jsonify({
                "message":
                    "This subject does not exist "
                    "in lecturers database."
            }), 400


        lecturer_name = lecturer["name"]

        total_periods = int(
            lecturer["total_periods"]
        )


        # =================================================
        # CHECK SECTION
        # =================================================

        section_row = conn.execute("""
            SELECT id
            FROM timetable
            WHERE LOWER(TRIM(class_name))
                  = LOWER(TRIM(?))
            LIMIT 1
        """, (
            section,
        )).fetchone()


        if section_row is None:

            return jsonify({
                "message":
                    "This section does not exist "
                    "in timetable database."
            }), 400


        # =================================================
        # DUPLICATE SUBJECT + SECTION
        # =================================================

        duplicate = conn.execute("""
            SELECT id
            FROM subjects
            WHERE LOWER(TRIM(subject))
                  = LOWER(TRIM(?))
            AND LOWER(TRIM(section_name))
                  = LOWER(TRIM(?))
            LIMIT 1
        """, (
            subject,
            section
        )).fetchone()


        if duplicate is not None:

            return jsonify({
                "message":
                    "This subject already exists "
                    "for this section."
            }), 400


        # =================================================
        # GET KIM
        #
        # All LAB values belonging to all subjects
        # taught by the same lecturer.
        # =================================================

        kim = get_kim_array(
            conn,
            lecturer_name
        )


        kim_pairs = get_kim_pairs(
            kim
        )


        # =================================================
        # CHECK CURRENT SUBJECT COUNT
        # =================================================

        current_occurrences = (
            get_subject_occurrences(
                conn,
                section,
                subject
            )
        )


        current_count = len(
            current_occurrences
        )


        if current_count > total_periods:

            return jsonify({
                "message":
                    "Timetable is filled incorrectly. "
                    "The subject '" +
                    subject +
                    "' appears " +
                    str(current_count) +
                    " times in section '" +
                    section +
                    "', but total periods is " +
                    str(total_periods) +
                    ". Please check the timetable."
            }), 400


        # =================================================
        # INSERT SUBJECT RECORD FIRST
        #
        # LAB initially 0.
        # =================================================

        cursor = conn.execute("""
            INSERT INTO subjects
            (
                subject,
                section_name,
                lab
            )
            VALUES (?, ?, ?)
        """, (
            subject,
            section,
            0
        ))


        subject_id = cursor.lastrowid


        # =================================================
        # AUTOMATIC TIMETABLE PROCESS
        # =================================================

        result = assign_subject(
            conn,
            subject,
            section,
            kim_pairs
        )


        # =================================================
        # GET FINAL LOCATIONS
        # =================================================

        combinations = (
            result["occurrences"]
        )


        lab_string = make_lab_from_occurrences(
            combinations
        )


        lab_value = (
            int(lab_string)
            if lab_string
            else 0
        )


        # =================================================
        # SAVE LAB
        # =================================================

        conn.execute("""
            UPDATE subjects
            SET lab = ?
            WHERE id = ?
        """, (
            lab_value,
            subject_id
        ))


        conn.commit()


        return jsonify({

            "message":
                "Subject saved successfully.",

            "id":
                subject_id,

            "subject":
                subject,

            "section_name":
                section,

            "lecturer":
                lecturer_name,

            "total_periods":
                total_periods,

            "added":
                result["added"],

            "lab":
                lab_value

        }), 201


    except ValueError as error:

        conn.rollback()

        return jsonify({
            "message":
                str(error)
        }), 400


    except Exception as error:

        conn.rollback()

        print(
            "ADD SUBJECT ERROR:",
            error
        )

        return jsonify({
            "message":
                "Server error while creating subject."
        }), 500


    finally:

        conn.close()


# =========================================================
# DELETE SUBJECT
# =========================================================

@app.route(
    "/api/subjects/<int:subject_id>",
    methods=["DELETE"]
)
def delete_subject(subject_id):

    conn = get_db()


    try:

        # =================================================
        # GET RECORD
        # =================================================

        row = conn.execute("""
            SELECT
                subject,
                section_name
            FROM subjects
            WHERE id = ?
        """, (
            subject_id,
        )).fetchone()


        if row is None:

            return jsonify({
                "message":
                    "Subject record not found."
            }), 404


        subject = row["subject"]

        section = row["section_name"]


        # =================================================
        # CLEAR TIMETABLE
        # =================================================

        conn.execute("""
            UPDATE timetable
            SET
                subject = NULL,
                room_name = NULL
            WHERE LOWER(TRIM(class_name))
                  = LOWER(TRIM(?))
            AND LOWER(TRIM(subject))
                  = LOWER(TRIM(?))
        """, (
            section,
            subject
        ))


        # =================================================
        # DELETE SUBJECT RECORD
        # =================================================

        conn.execute("""
            DELETE FROM subjects
            WHERE id = ?
        """, (
            subject_id,
        ))


        conn.commit()


        return jsonify({

            "message":
                "Subject deleted and timetable "
                "locations cleared."

        })


    except Exception as error:

        conn.rollback()

        print(
            "DELETE ERROR:",
            error
        )

        return jsonify({
            "message":
                "Unable to delete subject."
        }), 500


    finally:

        conn.close()


# =========================================================
# UPDATE LAB
# =========================================================
#
# Only LAB is updated.
#
# It takes all occurrences of this subject in its section.
#
# Example:
#
# Wednesday 6 -> 36
# Friday 1    -> 51
#
# LAB = 3651
#
# Then checks:
#
# 36
# 51
#
# against every two-digit combination in the other
# LAB values belonging to the same lecturer.
#
# =========================================================

@app.route(
    "/api/subjects/<int:subject_id>",
    methods=["PUT"]
)
def update_subject(subject_id):

    data = request.get_json() or {}


    if data.get("update_lab") is not True:

        return jsonify({
            "message":
                "Only LAB update is allowed."
        }), 400


    conn = get_db()


    try:

        # =================================================
        # GET SUBJECT RECORD
        # =================================================

        record = conn.execute("""
            SELECT
                id,
                subject,
                section_name,
                lab
            FROM subjects
            WHERE id = ?
        """, (
            subject_id,
        )).fetchone()


        if record is None:

            return jsonify({
                "message":
                    "Subject record not found."
            }), 404


        subject = record["subject"]

        section = record["section_name"]


        # =================================================
        # GET LECTURER
        # =================================================

        lecturer = get_lecturer_for_subject(
            conn,
            subject
        )


        if lecturer is None:

            return jsonify({
                "message":
                    "Subject was not found in "
                    "lecturers database."
            }), 400


        lecturer_name = lecturer["name"]


        # =================================================
        # GET CURRENT OCCURRENCES
        # =================================================

        occurrences = (
            get_subject_occurrences(
                conn,
                section,
                subject
            )
        )


        # =================================================
        # CREATE NEW LAB
        # =================================================

        new_lab_string = (
            make_lab_from_occurrences(
                occurrences
            )
        )


        new_lab = (
            int(new_lab_string)
            if new_lab_string
            else 0
        )


        # =================================================
        # GET OTHER LAB VALUES
        #
        # IMPORTANT:
        #
        # Current record is excluded.
        #
        # This prevents the current LAB from
        # conflicting with itself.
        # =================================================

        kim = get_kim_array(
            conn,
            lecturer_name,
            exclude_id=subject_id
        )


        kim_pairs = get_kim_pairs(
            kim
        )


        # =================================================
        # CHECK EVERY TWO-DIGIT COMBINATION
        # =================================================

        conflicts = []


        for combination in occurrences:

            if combination in kim_pairs:

                conflicts.append(
                    combination
                )


        # =================================================
        # CONFLICT FOUND
        # =================================================

        if conflicts:

            conflict_text = ", ".join(
                str(x)
                for x in conflicts
            )


            return jsonify({

                "message":
                    "Manual update error. "
                    "The LAB cannot be updated because "
                    "the timetable location(s) " +
                    conflict_text +
                    " already exist in another LAB "
                    "belonging to lecturer '" +
                    lecturer_name +
                    "'."

            }), 409


        # =================================================
        # UPDATE LAB
        # =================================================

        conn.execute("""
            UPDATE subjects
            SET lab = ?
            WHERE id = ?
        """, (
            new_lab,
            subject_id
        ))


        conn.commit()


        return jsonify({

            "message":
                "LAB updated successfully.",

            "id":
                subject_id,

            "subject":
                subject,

            "section_name":
                section,

            "lab":
                new_lab

        }), 200


    except Exception as error:

        conn.rollback()

        print(
            "UPDATE LAB ERROR:",
            error
        )

        return jsonify({
            "message":
                "Unable to update LAB."
        }), 500


    finally:

        conn.close()


@app.route("/api/lecturer-timetable/<lecturer_name>")
def lecturer_timetable(lecturer_name):
  
    conn = get_db()
    cursor = conn.cursor()

    try:

        # ==========================================
        # 1. GET ALL SUBJECTS FOR THIS LECTURER
        # ==========================================

        cursor.execute("""
            SELECT subject
            FROM lecturers
            WHERE LOWER(name) = LOWER(?)
        """, (lecturer_name,))

        lecturer_rows = cursor.fetchall()


        if not lecturer_rows:

            return jsonify({
                "message": "Lecturer not found"
            }), 404


        # ==========================================
        # TIMETABLE RESULT
        # ==========================================

        timetable = {}

        subjects_found = []


        # ==========================================
        # 2. PROCESS EVERY SUBJECT OF LECTURER
        # ==========================================

        for lecturer_row in lecturer_rows:

            subject = lecturer_row["subject"]

            if not subject:
                continue


            subjects_found.append(subject)


            # ======================================
            # 3. FIND ALL SECTIONS OF THIS SUBJECT
            # ======================================

            cursor.execute("""
                SELECT section_name, lab
                FROM subjects
                WHERE LOWER(subject) = LOWER(?)
            """, (subject,))

            subject_rows = cursor.fetchall()


            # ======================================
            # 4. PROCESS EVERY SECTION
            # ======================================

            for subject_row in subject_rows:

                section_name = subject_row["section_name"]

                lab = subject_row["lab"]


                if not section_name:
                    continue


                if lab is None:
                    continue


                # Convert lab to string
                lab_string = str(lab).strip()


                # Lab = 0 means no timetable position
                if lab_string == "0" or lab_string == "":
                    continue


                # ==================================
                # 5. READ LAB TWO DIGITS AT A TIME
                # ==================================

                for i in range(
                    0,
                    len(lab_string) - 1,
                    2
                ):

                    pair = lab_string[i:i + 2]


                    # Must contain exactly 2 digits
                    if len(pair) != 2:
                        continue


                    if not pair.isdigit():
                        continue


                    day = int(pair[0])

                    period = int(pair[1])


                    # ==================================
                    # VALID DAY / PERIOD
                    # ==================================

                    if day < 1 or day > 6:
                        continue


                    if period < 1 or period > 7:
                        continue


                    # ==================================
                    # CREATE KEY
                    # ==================================

                    key = f"{day}{period}"


                    if key not in timetable:

                        timetable[key] = []


                    # ==================================
                    # ADD SECTION
                    # ==================================

                    if section_name not in timetable[key]:

                        timetable[key].append(
                            section_name
                        )


        # ==========================================
        # REMOVE DUPLICATE SUBJECTS
        # ==========================================

        subjects_found = list(
            dict.fromkeys(subjects_found)
        )


        # ==========================================
        # RETURN DATA
        # ==========================================

        return jsonify({

            "lecturer": lecturer_name,

            "subjects": subjects_found,

            "timetable": timetable

        })


    except Exception as e:

        print("LECTURER TIMETABLE ERROR:", e)

        return jsonify({

            "message":
                "Server error while creating lecturer timetable",

            "error":
                str(e)

        }), 500


    finally:

        conn.close()

@app.route("/api/lecturer/suggestions")
def lecturer_suggestions():

    conn = get_db()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT DISTINCT name
            FROM lecturers
            WHERE name IS NOT NULL
              AND TRIM(name) != ''
            ORDER BY name
        """)

        rows = cursor.fetchall()


        lecturers = [
            row[0]
            for row in rows
        ]


        return jsonify(lecturers)


    except Exception as e:

        print("LECTURER SUGGESTION ERROR:", e)

        return jsonify({
            "message": "Unable to load lecturers"
        }), 500


    finally:

        conn.close()






# ==========================================
# GET ALL DIFFERENT CLASS NAMES
# ==========================================

@app.route("/api/classes", methods=["GET"])
def get_classes():

    conn = get_db()

    rows = conn.execute("""
        SELECT DISTINCT class_name
        FROM timetable
        ORDER BY class_name
    """).fetchall()

    conn.close()

    classes = [
        row["class_name"]
        for row in rows
    ]

    return jsonify(classes)


# ==========================================
# ADD CLASS
# ==========================================

@app.route("/api/classes", methods=["POST"])
def add_class():

    data = request.get_json()

    class_name = data.get("class_name", "").strip()


    if not class_name:

        return jsonify({
            "message": "Class name is required"
        }), 400


    conn = get_db()


    # Check whether class already exists

    existing = conn.execute("""
        SELECT 1
        FROM timetable
        WHERE class_name = ?
        LIMIT 1
    """, (class_name,)).fetchone()


    if existing:

        conn.close()

        return jsonify({
            "message": "Class already exists"
        }), 409


    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]


    # Create 42 combinations

    for day in days:

        for period in range(1, 8):

            conn.execute("""
                INSERT INTO timetable
                (
                    class_name,
                    subject,
                    room_name,
                    day,
                    period_no
                )
                VALUES (?, NULL, NULL, ?, ?)
            """, (
                class_name,
                day,
                period
            ))


    conn.commit()

    conn.close()


    return jsonify({

        "message":
            "Class created successfully",

        "class_name":
            class_name,

        "rows_created":
            42

    })


# ==========================================
# DELETE CLASS
# ==========================================

@app.route(
    "/api/classes/<path:class_name>",
    methods=["DELETE"]
)
def delete_class(class_name):

    conn = get_db()


    existing = conn.execute("""
        SELECT 1
        FROM timetable
        WHERE class_name = ?
        LIMIT 1
    """, (class_name,)).fetchone()


    if not existing:

        conn.close()

        return jsonify({
            "message": "Class not found"
        }), 404


    conn.execute("""
        DELETE FROM timetable
        WHERE class_name = ?
    """, (class_name,))


    conn.commit()

    conn.close()


    return jsonify({

        "message":
            "Class deleted successfully"

    })

# ==========================================
# GET TIMETABLE FOR A CLASS
# ==========================================

@app.route(
    "/api/timetable/class/<path:class_name>",
    methods=["GET"]
)
def get_timetable(class_name):

    conn = get_db()

    rows = conn.execute("""
        SELECT
            id,
            class_name,
            subject,
            room_name,
            day,
            period_no
        FROM timetable
        WHERE class_name = ?
        ORDER BY
            CASE day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
            END,
            period_no
    """, (class_name,)).fetchall()

    conn.close()

    if not rows:

        return jsonify({
            "message": "Class not found"
        }), 404


    timetable = []

    for row in rows:

        timetable.append({

            "id": row["id"],

            "class_name":
                row["class_name"],

            "subject":
                row["subject"],

            "room_name":
                row["room_name"],

            "day":
                row["day"],

            "period_no":
                row["period_no"]

        })


    return jsonify(timetable)

# ==========================================
# SAVE / UPDATE TIMETABLE
# ==========================================

@app.route(
    "/api/timetable/class/<path:class_name>",
    methods=["PUT"]
)
def update_timetable(class_name):

    data = request.get_json()


    if not data:

        return jsonify({
            "message": "No data received"
        }), 400


    timetable_data = data.get("timetable")


    if not isinstance(
        timetable_data,
        list
    ):

        return jsonify({
            "message":
                "Invalid timetable data"
        }), 400


    conn = get_db()


    # ======================================
    # CHECK CLASS
    # ======================================

    existing = conn.execute("""
        SELECT 1
        FROM timetable
        WHERE class_name = ?
        LIMIT 1
    """, (class_name,)).fetchone()


    if not existing:

        conn.close()

        return jsonify({
            "message":
                "Class not found"
        }), 404


    # ======================================
    # UPDATE EACH CELL
    # ======================================

    for item in timetable_data:


        day =           item.get("day")

        period_no =           item.get("period_no")


        subject = item.get("subject")


        room_name = item.get("room_name")


        # Convert empty strings to NULL

        if subject == "":
            subject = None


        if room_name == "":
            room_name = None


        conn.execute("""
            UPDATE timetable

            SET
                subject = ?,
                room_name = ?

            WHERE
                class_name = ?
                AND day = ?
                AND period_no = ?

        """, (

            subject,

            room_name,

            class_name,

            day,

            period_no

        ))


    conn.commit()

    conn.close()


    return jsonify({

        "message":
            "Timetable updated successfully",

        "class_name":
            class_name

    })

# =================================
# GET ALL LECTURERS
# =================================

@app.route("/api/lecturers", methods=["GET"])
def get_lecturers():

    conn = get_db()

    rows = conn.execute("""
        SELECT
            id,
            name,
            subject,
            total_periods,
            total_sections
        FROM lecturers
        ORDER BY id
    """).fetchall()

    conn.close()

    lecturers = []

    for row in rows:

        lecturers.append({

            "id": row["id"],

            "name": row["name"],

            "subject": row["subject"],

            "total_periods":
                row["total_periods"],

            "total_sections":
                row["total_sections"]

        })

    return jsonify(lecturers)


# =================================
# ADD LECTURER
# =================================

@app.route("/api/lecturers", methods=["POST"])
def add_lecturer():

    data = request.get_json()


    if not data:

        return jsonify({
            "message": "No data received"
        }), 400


    name = data.get("name")
    subject = data.get("subject")

    total_periods =        data.get("total_periods")

    total_sections =   data.get("total_sections")


    if not name:

        return jsonify({
            "message": "Lecturer name is required"
        }), 400


    if not subject:

        return jsonify({
            "message": "Subject is required"
        }), 400


    if total_periods is None:

        return jsonify({
            "message": "Total periods is required"
        }), 400


    if total_sections is None:

        return jsonify({
            "message": "Total sections is required"
        }), 400


    try:

        total_periods =            int(total_periods)

        total_sections =  int(total_sections)

    except (ValueError, TypeError):

        return jsonify({
            "message":
                "Periods and sections must be integers"
        }), 400


    if total_periods < 0:

        return jsonify({
            "message":
                "Total periods cannot be negative"
        }), 400


    if total_sections < 0:

        return jsonify({
            "message":
                "Total sections cannot be negative"
        }), 400


    conn = get_db()


    conn.execute("""
        INSERT INTO lecturers
        (
            name,
            subject,
            total_periods,
            total_sections
        )
        VALUES (?, ?, ?, ?)
    """, (
        name.strip(),
        subject.strip(),
        total_periods,
        total_sections
    ))


    conn.commit()

    conn.close()


    return jsonify({
        "message":
            "Lecturer added successfully"
    }), 201


# =================================
# DELETE LECTURER
# =================================

@app.route(
    "/api/lecturers/<int:lecturer_id>",
    methods=["DELETE"]
)
def delete_lecturer(lecturer_id):

    conn = get_db()


    cursor = conn.execute("""
        DELETE FROM lecturers
        WHERE id = ?
    """, (lecturer_id,))


    if cursor.rowcount == 0:

        conn.close()

        return jsonify({
            "message":
                "Lecturer not found"
        }), 404


    conn.commit()

    conn.close()


    return jsonify({
        "message":
            "Lecturer deleted successfully"
    })


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

