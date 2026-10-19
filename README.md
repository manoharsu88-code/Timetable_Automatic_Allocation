# Automated Timetable Scheduler & Lecturer Workload Management System

An intelligent academic scheduling platform built with Flask and SQLite that automates timetable generation, prevents scheduling collisions, tracks faculty workloads, and manages exam schedules.

---

## Overview

Managing university and college timetables manually often leads to overlapping schedules, lecturer double-booking, uneven workload distribution and takes long time for large datasets. 

This platform uses a coordinate-based location encoding algorithm (Day-Period matrix) to ensure conflict-free timetable generation across multiple sections, departments, and faculty workloads. Administrators can generate timetables automatically, make manual adjustments, schedule multi-period lab sessions, assign weekly tests, and inspect each faculty member's weekly commitments in real time.

---

## Key Features

### 1. Conflict-Free Timetable Allocation
- **Automated Period Placement**: Allocates subject periods to empty slots in a class section without overlapping existing classes.
- **Zero Double-Booking for Lecturers**: Uses an internal conflict matrix (`KIM`) that tracks all assigned slots for a lecturer across all subjects and sections, ensuring no lecturer is scheduled in two places at the same time.
- **Consecutive Multi-Period Block Allocation**: Supports continuous blocks (e.g., 3-hour lab sessions) using systematic and randomized block-search algorithms.

### 2. Location-Based Period Encoding Algorithm
- Timetable slots are mapped to a two-digit integer formula:
  $$\text{Address} = (\text{Day Number} \times 10) + \text{Period Number}$$
  - **Days**: Monday (`1`) through Saturday (`6`)
  - **Periods**: Period 1 through Period 7
  - *Example*: Wednesday (Day 3), Period 4 maps to location code `34`.
- All period allocations for a subject in a section are concatenated into a single compact integer (stored in the `lab` column of the `subjects` table). For example, `2225264652` represents allocations on Tuesday Period 2 (`22`), Tuesday Period 5 (`25`), Tuesday Period 6 (`26`), Thursday Period 6 (`46`), and Friday Period 2 (`52`).

### 3. Faculty Workload & Timetable Inspection
- Dedicated dashboard to view personalized schedules for any lecturer (`/api/lecturer-timetable/<lecturer_name>`).
- Visualizes the total periods taught and sections assigned per week.
- Prevents assigning more periods than the lecturer's workload limit (`total_periods`).

### 4. Weekly Test & Examination Scheduling
- Bulk-assigns weekly tests across class sections for designated days and period ranges (e.g., Wednesday Periods 1–2).
- Automatically marks period slots as `Weekly Test`, clears room conflicts, and recalculates availability.

### 5. Multi-Section Lecturer Allocation
- Distributes sections randomly or systematically among available faculty members while maintaining section capacity constraints.

### 6. Role-Based Access Control (RBAC)
- Multi-role login system supporting **Admin**, **Lecturer**, and **Student**.
- Session-managed dashboards and protected API endpoints.

---

## System Architecture & Workflow
                              +-----------------------+
                              |   Admin / User Login  |
                              +-----------+-----------+
                                          |
                                          v
                     +-----------------------------------------+
                     |  Define Faculty, Sections & Constraints |
                     |  - Lecturers & Subjects                 |
                     |  - Max Periods & Section Allocations    |
                     +--------------------+--------------------+
                                          |
                    +---------------------+---------------------+
                    |                                           |
                    v                                           v
    +---------------------------------+        +-----------------------------------+
    | Single-Period Theory Allocation |        | 3-Period Lab / Block Allocation   |
    +----------------+----------------+        +-----------------+-----------------+
                    |                                           |
                    +---------------------+---------------------+
                                          |
                                          v
                          +-------------------------------+
                          |    Conflict Evaluation Engine |
                          |    1. Is Section Slot Empty?  |
                          |    2. Is Slot in Faculty KIM? |
                          +---------------+---------------+
                                          |
                             +------------+------------+
                             |                         |
                          [No Conflict]           [Conflict Found]
                             |                         |
                             v                         v
               +---------------------------+  +--------------------------+
               | Assign Slot & Update Code |  | Attempt Alternative Slot |
               +-------------+-------------+  +--------------------------+
                             |
                             v
               +---------------------------+
               |  Timetable & DB Finalized |
               +---------------------------+

## Database Design

The system runs on SQLite (`total.db`) using the following core schema:

```sql
-- 1. Authentication & Roles
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'lecturer', 'student'))
);

-- 2. Faculty Profiles & Workload Limits
CREATE TABLE lecturers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    total_periods INTEGER NOT NULL,
    total_sections INTEGER NOT NULL
);

-- 3. Subject-to-Section Mapping & Concatenated Location Codes
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    section_name TEXT NOT NULL,
    lab INTEGER DEFAULT 0
);

-- 4. Master Weekly Timetable Grid
CREATE TABLE timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL,
    subject TEXT,
    room_name TEXT,
    day TEXT NOT NULL,
    period_no INTEGER NOT NULL
);

├── app.py                      # Core Flask backend, API endpoints & scheduling engine
├── total.db                    # SQLite database storing faculty, timetables, and users
└── templates/
    ├── login.html              # Role-based login page
    ├── mainpage.html           # Main navigation portal
    ├── admin.html              # Admin configuration dashboard
    ├── timetable.html          # Interactive timetable visualizer and editor
    ├── lecturers.html          # Faculty management and workload view
    ├── lecturer_sections.html  # Section-to-lecturer distribution
    ├── subjects.html           # Theory subject mapping interface
    ├── subjects_lab.html       # Lab / consecutive block allocation
    ├── classrooms.html         # Classroom management
    ├── lect.html               # Individual lecturer portal
    └── weekly_test.html        # Weekly test exam scheduler

Install Dependencies
Bash
pip install Flask

 Run the Application
Bash
python app.py
