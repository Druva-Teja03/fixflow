"""
Database Seeding Script for FixFlow.
Populates demo users, 25 realistic issues across multiple categories and blocks,
sample assignments, comments, supporters, and status histories.
"""

import os
import sys
import datetime
import random

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import (
    User,
    UserRole,
    Issue,
    IssueCategory,
    IssuePriority,
    IssueStatus,
    Assignment,
    Comment,
    IssueSupporter,
    StatusHistory,
    Notification,
)
from backend.app.security import get_password_hash


def seed_database():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already contains data. Cleaning and re-seeding...")
            db.query(Notification).delete()
            db.query(StatusHistory).delete()
            db.query(IssueSupporter).delete()
            db.query(Comment).delete()
            db.query(Assignment).delete()
            db.query(Issue).delete()
            db.query(User).delete()
            db.commit()
            for tbl in ["notifications", "status_history", "issue_supporters", "comments", "assignments", "issues", "users"]:
                db.execute(text(f"ALTER TABLE {tbl} AUTO_INCREMENT = 1;"))
            db.commit()

        print("Seeding users...")
        demo_password = get_password_hash("Demo@1234")

        # 1 Admin
        admin = User(
            name="Campus Administrator",
            email="admin@fixflow.demo",
            password_hash=demo_password,
            role=UserRole.ADMIN,
            team=None,
        )
        db.add(admin)

        # 3 Staff members
        staff_electrical = User(
            name="Ramesh Sharma",
            email="electric@fixflow.demo",
            password_hash=demo_password,
            role=UserRole.STAFF,
            team="Electrical",
        )
        staff_it = User(
            name="Suresh Kumar",
            email="it@fixflow.demo",
            password_hash=demo_password,
            role=UserRole.STAFF,
            team="IT",
        )
        staff_plumbing = User(
            name="Mahesh Gowda",
            email="plumbing@fixflow.demo",
            password_hash=demo_password,
            role=UserRole.STAFF,
            team="Plumbing",
        )
        db.add_all([staff_electrical, staff_it, staff_plumbing])

        # 5 Students
        students = [
            User(name="Aarav Patel", email="student1@fixflow.demo", password_hash=demo_password, role=UserRole.STUDENT),
            User(name="Ananya Iyer", email="student2@fixflow.demo", password_hash=demo_password, role=UserRole.STUDENT),
            User(name="Rahul Verma", email="student3@fixflow.demo", password_hash=demo_password, role=UserRole.STUDENT),
            User(name="Sneha Reddy", email="student4@fixflow.demo", password_hash=demo_password, role=UserRole.STUDENT),
            User(name="Vikram Singh", email="student5@fixflow.demo", password_hash=demo_password, role=UserRole.STUDENT),
        ]
        db.add_all(students)
        db.flush()  # assign user_ids

        all_staff = [staff_electrical, staff_it, staff_plumbing]
        now = datetime.datetime.now(datetime.timezone.utc)

        # Pre-defined realistic issues list
        issue_templates = [
            # Issue 1 (Near-duplicate target for testing)
            {
                "title": "Projector not working in Room 204",
                "desc": "The overhead projector does not turn on even when the power switch is flipped. The indicator light is blinking red.",
                "ai_summary": "Overhead projector power failure with red indicator light blinking.",
                "cat": IssueCategory.EQUIPMENT,
                "block": "Block A",
                "building": "Engineering Block / 2nd Floor",
                "room": "Room 204",
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.ASSIGNED,
                "days_ago": 2,
                "staff": staff_it,
            },
            # Issue 2 (Near-duplicate pair for Issue 1)
            {
                "title": "Broken projector / display not turning on",
                "desc": "Projector in Room 204 is not displaying anything. Power LED blinks red, cannot start lecture slides.",
                "ai_summary": "Projector display failure, unable to start lecture presentation.",
                "cat": IssueCategory.EQUIPMENT,
                "block": "Block A",
                "building": "Engineering Block / 2nd Floor",
                "room": "Room 204",
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.OPEN,
                "days_ago": 1,
                "staff": None,
            },
            # Issue 3 - Critical Electrical
            {
                "title": "Sparking socket in Computer Lab 3",
                "desc": "The main wall switchboard in Lab 3 produced sparks and a burning smell when a student plugged in their laptop charger.",
                "ai_summary": "Dangerous electrical sparking and burning smell from wall switchboard.",
                "cat": IssueCategory.ELECTRICAL,
                "block": "Block B",
                "building": "CS Building / 1st Floor",
                "room": "Lab 3",
                "priority": IssuePriority.CRITICAL,
                "status": IssueStatus.IN_PROGRESS,
                "days_ago": 3,
                "staff": staff_electrical,
            },
            # Issue 4 - High Plumbing
            {
                "title": "Severe water leakage in 2nd floor restroom",
                "desc": "Pipe joint burst under the sink causing continuous flooding on the floor. Water is leaking into the main hallway.",
                "ai_summary": "Pipe joint burst causing continuous flooding in restroom.",
                "cat": IssueCategory.PLUMBING,
                "block": "Block A",
                "building": "Main Academic / 2nd Floor",
                "room": "Washroom 202",
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.IN_PROGRESS,
                "days_ago": 4,
                "staff": staff_plumbing,
            },
            # Issue 5 - Internet
            {
                "title": "Campus Wi-Fi down in Central Library",
                "desc": "Neither FixFlow_Student nor Eduroam SSIDs are connecting. Access point appears to have lost power.",
                "ai_summary": "Complete Wi-Fi connectivity outage across Central Library.",
                "cat": IssueCategory.INTERNET,
                "block": "Block C",
                "building": "Library Building / Ground Floor",
                "room": "Reading Hall",
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.OPEN,
                "days_ago": 1,
                "staff": None,
            },
            # Issue 6 - Cleaning
            {
                "title": "Spilled drinks and trash near Canteen exit",
                "desc": "Large spill of sweet tea and overflowing trash bins attracting flies and creating a slippery hazard.",
                "ai_summary": "Trash overflow and drink spill creating slippery hazard near canteen.",
                "cat": IssueCategory.CLEANING,
                "block": "Block D",
                "building": "Student Center",
                "room": "Canteen Exit Gate",
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.RESOLVED,
                "days_ago": 7,
                "resolved_days_ago": 6,
                "staff": None,
            },
            # Issue 7 - Furniture
            {
                "title": "Broken wooden bench with sharp protruding nail",
                "desc": "Bench in row 4 has a cracked backrest and a sharp nail protruding from the side. Potential injury risk.",
                "ai_summary": "Broken bench backrest with exposed sharp nail.",
                "cat": IssueCategory.FURNITURE,
                "block": "Block B",
                "building": "Science Block / 3rd Floor",
                "room": "Room 310",
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.ASSIGNED,
                "days_ago": 5,
                "staff": staff_electrical,  # or general maintenance
            },
            # Issue 8 - Doors/Windows
            {
                "title": "Window latch broken in Seminar Hall 1",
                "desc": "The large glass window cannot be securely latched and bangs violently when winds pick up.",
                "ai_summary": "Window latch broken in seminar hall causing rattling in wind.",
                "cat": IssueCategory.DOORS_WINDOWS,
                "block": "Block C",
                "building": "Auditorium Complex",
                "room": "Seminar Hall 1",
                "priority": IssuePriority.LOW,
                "status": IssueStatus.RESOLVED,
                "days_ago": 12,
                "resolved_days_ago": 10,
                "staff": staff_electrical,
            },
            # Issue 9 - Electrical
            {
                "title": "Ceiling fan making loud screeching noise",
                "desc": "Middle ceiling fan in Lecture Hall 101 vibrates violently and emits a loud metallic screeching noise.",
                "ai_summary": "Ceiling fan vibrating violently with loud metallic noise.",
                "cat": IssueCategory.ELECTRICAL,
                "block": "Block A",
                "building": "Main Academic / 1st Floor",
                "room": "Room 101",
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.OPEN,
                "days_ago": 6,
                "staff": None,
            },
            # Issue 10 - Plumbing
            {
                "title": "Drinking water cooler tap leaking continuously",
                "desc": "The push tap on the 3rd floor water cooler is stuck open and draining clean drinking water constantly.",
                "ai_summary": "Water cooler tap stuck open wasting drinking water.",
                "cat": IssueCategory.PLUMBING,
                "block": "Block B",
                "building": "CS Building / 3rd Floor",
                "room": "Corridor near 305",
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.RESOLVED,
                "days_ago": 15,
                "resolved_days_ago": 14,
                "staff": staff_plumbing,
            },
            # Issue 11 - Equipment
            {
                "title": "Smart Board touch calibration off by 6 inches",
                "desc": "Interactive smartboard in smart classroom 104 has lost touch accuracy. Impossible to draw or write notes.",
                "ai_summary": "Smart board touch calibration severely misaligned.",
                "cat": IssueCategory.EQUIPMENT,
                "block": "Block A",
                "building": "Engineering Block / 1st Floor",
                "room": "Smart Classroom 104",
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.ASSIGNED,
                "days_ago": 8,
                "staff": staff_it,
            },
            # Issue 12 - Critical Electrical
            {
                "title": "Exposed high voltage wire near staircase",
                "desc": "Conduit pipe has detached exposing live electrical wires right next to the handrail on staircase B.",
                "ai_summary": "Exposed electrical wiring hanging beside staircase handrail.",
                "cat": IssueCategory.ELECTRICAL,
                "block": "Block C",
                "building": "Academic Block C",
                "room": "Staircase B (2nd to 3rd floor)",
                "priority": IssuePriority.CRITICAL,
                "status": IssueStatus.RESOLVED,
                "days_ago": 20,
                "resolved_days_ago": 19,
                "staff": staff_electrical,
            },
            # Issue 13 - Cleaning
            {
                "title": "Whiteboard permanently stained with permanent marker",
                "desc": "Someone used permanent marker on the main board in Room 206. Needs professional cleaning solvent.",
                "ai_summary": "Whiteboard stained with permanent marker requiring solvent clean.",
                "cat": IssueCategory.CLEANING,
                "block": "Block A",
                "building": "Main Academic / 2nd Floor",
                "room": "Room 206",
                "priority": IssuePriority.LOW,
                "status": IssueStatus.OPEN,
                "days_ago": 2,
                "staff": None,
            },
            # Issue 14 - Furniture
            {
                "title": "Desk drawers jammed in Faculty Lounge",
                "desc": "Three shared desk drawers cannot be pulled open. Handles have come off.",
                "ai_summary": "Desk drawers jammed and handles broken.",
                "cat": IssueCategory.FURNITURE,
                "block": "Block B",
                "building": "Administration / 2nd Floor",
                "room": "Room 214",
                "priority": IssuePriority.LOW,
                "status": IssueStatus.RESOLVED,
                "days_ago": 18,
                "resolved_days_ago": 16,
                "staff": staff_electrical,
            },
            # Issue 15 - Internet
            {
                "title": "Ethernet port 12 dead in Networking Lab",
                "desc": "Cable test shows no link light on port 12. Student workstation cannot reach local switch.",
                "ai_summary": "Ethernet wall port dead in networking lab.",
                "cat": IssueCategory.INTERNET,
                "block": "Block B",
                "building": "CS Building / 2nd Floor",
                "room": "Lab 205",
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.IN_PROGRESS,
                "days_ago": 4,
                "staff": staff_it,
            },
            # Issue 16 - Doors/Windows
            {
                "title": "Main entrance glass door handle loose",
                "desc": "Heavy glass entrance door handle is wobbly and feels like it might detach completely.",
                "ai_summary": "Glass entrance door handle loose and wobbly.",
                "cat": IssueCategory.DOORS_WINDOWS,
                "block": "Block D",
                "building": "Student Center / Ground Floor",
                "room": "Main Entrance",
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.ASSIGNED,
                "days_ago": 9,
                "staff": staff_electrical,
            },
            # Issue 17 - Plumbing
            {
                "title": "Low water pressure in 4th floor chemistry labs",
                "desc": "Emergency eye wash station and sink taps have barely any water flow.",
                "ai_summary": "Extremely low water pressure affecting eye wash station in lab.",
                "cat": IssueCategory.PLUMBING,
                "block": "Block C",
                "building": "Science Block / 4th Floor",
                "room": "Chemistry Lab 402",
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.OPEN,
                "days_ago": 5,
                "staff": None,
            },
            # Issue 18 - Equipment
            {
                "title": "Microphone in Auditorium cutting in and out",
                "desc": "Wireless podium microphone experiences heavy audio crackle and cuts out every 30 seconds.",
                "ai_summary": "Podium wireless microphone audio crackling and dropping out.",
                "cat": IssueCategory.EQUIPMENT,
                "block": "Block D",
                "building": "Main Auditorium",
                "room": "Stage Area",
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.RESOLVED,
                "days_ago": 22,
                "resolved_days_ago": 21,
                "staff": staff_it,
            },
            # Issue 19 - Electrical
            {
                "title": "Flickering tube lights causing headaches",
                "desc": "Two 40W fluorescent lights at the back of Room 108 flicker continuously.",
                "ai_summary": "Fluorescent lights flickering continuously in lecture room.",
                "cat": IssueCategory.ELECTRICAL,
                "block": "Block A",
                "building": "Main Academic / 1st Floor",
                "room": "Room 108",
                "priority": IssuePriority.LOW,
                "status": IssueStatus.OPEN,
                "days_ago": 11,
                "staff": None,
            },
            # Issue 20 - Other
            {
                "title": "Stray dog entering ground floor corridor",
                "desc": "Broken boundary fence allows stray animals to wander into the corridor during evening classes.",
                "ai_summary": "Damaged fence allows stray dogs into academic corridor.",
                "cat": IssueCategory.OTHER,
                "block": "Block D",
                "building": "Rear Campus Gate",
                "room": "Ground Floor Corridor",
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.RESOLVED,
                "days_ago": 25,
                "resolved_days_ago": 23,
                "staff": staff_electrical,
            },
            # Issue 21 - Critical Plumbing
            {
                "title": "Severely blocked sewer line causing foul odor",
                "desc": "Ground floor drainage backing up and overflowing onto the outdoor walkway. Extreme smell.",
                "ai_summary": "Sewer line backup overflowing on outdoor walkway with foul odor.",
                "cat": IssueCategory.PLUMBING,
                "block": "Block A",
                "building": "Main Academic / Ground Floor",
                "room": "Rear Courtyard",
                "priority": IssuePriority.CRITICAL,
                "status": IssueStatus.RESOLVED,
                "days_ago": 28,
                "resolved_days_ago": 27,
                "staff": staff_plumbing,
            },
            # Issue 22 - Furniture
            {
                "title": "Library study carrel partition collapsed",
                "desc": "Wooden divider between study desks 14 and 15 has fallen over.",
                "ai_summary": "Study desk wooden divider collapsed.",
                "cat": IssueCategory.FURNITURE,
                "block": "Block C",
                "building": "Library Building / 1st Floor",
                "room": "Study Section B",
                "priority": IssuePriority.LOW,
                "status": IssueStatus.OPEN,
                "days_ago": 14,
                "staff": None,
            },
            # Issue 23 - Equipment
            {
                "title": "AC unit leaking water inside Server Room",
                "desc": "Duct AC in server closet is dripping condensation directly above the primary network rack.",
                "ai_summary": "AC condensation dripping directly above primary server rack.",
                "cat": IssueCategory.EQUIPMENT,
                "block": "Block B",
                "building": "CS Building / 1st Floor",
                "room": "Server Room B10",
                "priority": IssuePriority.CRITICAL,
                "status": IssueStatus.IN_PROGRESS,
                "days_ago": 1,
                "staff": staff_it,
            },
            # Issue 24 - Cleaning
            {
                "title": "Restroom soap dispensers completely empty",
                "desc": "All 4 liquid soap dispensers in Block B 2nd floor restrooms have been empty for two days.",
                "ai_summary": "Liquid soap dispensers empty in 2nd floor restroom.",
                "cat": IssueCategory.CLEANING,
                "block": "Block B",
                "building": "CS Building / 2nd Floor",
                "room": "Restroom 210",
                "priority": IssuePriority.LOW,
                "status": IssueStatus.RESOLVED,
                "days_ago": 16,
                "resolved_days_ago": 15,
                "staff": None,
            },
            # Issue 25 - Doors/Windows
            {
                "title": "Fire exit door jammed shut",
                "desc": "Push bar on the emergency exit door is rusted and will not unlatch when pressed firmly.",
                "ai_summary": "Emergency exit push bar jammed shut creating safety violation.",
                "cat": IssueCategory.DOORS_WINDOWS,
                "block": "Block A",
                "building": "Engineering Block / 1st Floor",
                "room": "East Fire Exit",
                "priority": IssuePriority.CRITICAL,
                "status": IssueStatus.ASSIGNED,
                "days_ago": 3,
                "staff": staff_electrical,
            }
        ]

        print(f"Seeding {len(issue_templates)} issues with timelines...")
        created_issues = []

        for idx, item in enumerate(issue_templates):
            reporter = students[idx % len(students)]
            created_dt = now - datetime.timedelta(days=item["days_ago"], hours=random.randint(1, 10))
            resolved_dt = None
            if item["status"] == IssueStatus.RESOLVED:
                r_days = item.get("resolved_days_ago", item["days_ago"] - 1)
                resolved_dt = now - datetime.timedelta(days=r_days, hours=random.randint(1, 8))

            issue = Issue(
                user_id=reporter.user_id,
                title=item["title"],
                description=item["desc"],
                ai_summary=item["ai_summary"],
                category=item["cat"],
                block=item["block"],
                building=item["building"],
                room=item["room"],
                priority=item["priority"],
                status=item["status"],
                image_url=None,
                ai_category=item["cat"].value,
                ai_priority=item["priority"].value,
                support_count=3 if idx == 0 else (2 if idx in [4, 11] else 1),
                created_at=created_dt,
                updated_at=resolved_dt or created_dt,
                resolved_at=resolved_dt,
            )
            db.add(issue)
            db.flush()
            created_issues.append((issue, item, created_dt, resolved_dt))

        # Add assignments, status history, comments, and supporters
        for issue, item, created_dt, resolved_dt in created_issues:
            # Initial status history: Created as Open
            db.add(
                StatusHistory(
                    issue_id=issue.issue_id,
                    old_status=None,
                    new_status="Open",
                    changed_by=issue.user_id,
                    changed_at=created_dt,
                )
            )

            # If assigned or beyond
            assigned_staff = item.get("staff")
            if item["status"] in [IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED] and assigned_staff:
                assigned_dt = created_dt + datetime.timedelta(hours=2)
                db.add(
                    Assignment(
                        issue_id=issue.issue_id,
                        staff_id=assigned_staff.user_id,
                        assigned_by=admin.user_id,
                        assigned_at=assigned_dt,
                    )
                )
                db.add(
                    StatusHistory(
                        issue_id=issue.issue_id,
                        old_status="Open",
                        new_status="Assigned",
                        changed_by=admin.user_id,
                        changed_at=assigned_dt,
                    )
                )

            # If in progress or resolved
            if item["status"] in [IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED]:
                inp_dt = created_dt + datetime.timedelta(hours=6)
                actor_id = assigned_staff.user_id if assigned_staff else admin.user_id
                db.add(
                    StatusHistory(
                        issue_id=issue.issue_id,
                        old_status="Assigned",
                        new_status="In Progress",
                        changed_by=actor_id,
                        changed_at=inp_dt,
                    )
                )

            # If resolved
            if item["status"] == IssueStatus.RESOLVED and resolved_dt:
                actor_id = assigned_staff.user_id if assigned_staff else admin.user_id
                db.add(
                    StatusHistory(
                        issue_id=issue.issue_id,
                        old_status="In Progress",
                        new_status="Resolved",
                        changed_by=actor_id,
                        changed_at=resolved_dt,
                    )
                )
                db.add(
                    Comment(
                        issue_id=issue.issue_id,
                        user_id=actor_id,
                        comment="Issue has been inspected and resolved. Equipment is back in working order.",
                        created_at=resolved_dt,
                    )
                )

            # Add student supporters for issues with support_count > 1
            if issue.support_count > 1:
                # Add (support_count - 1) distinct supporters
                for s_offset in range(1, issue.support_count):
                    db.add(
                        IssueSupporter(
                            issue_id=issue.issue_id,
                            user_id=students[(issue.user_id + s_offset) % len(students)].user_id,
                            created_at=created_dt + datetime.timedelta(hours=s_offset),
                        )
                    )

        db.commit()
        print("Database seeding completed successfully!")
        print("Demo Accounts:")
        print("  Admin:              admin@fixflow.demo     (Password: Demo@1234)")
        print("  Staff (Electrical): electric@fixflow.demo  (Password: Demo@1234)")
        print("  Staff (IT):         it@fixflow.demo        (Password: Demo@1234)")
        print("  Staff (Plumbing):   plumbing@fixflow.demo  (Password: Demo@1234)")
        print("  Student:            student1@fixflow.demo  (Password: Demo@1234)")
        print(f"Total issues seeded: {len(created_issues)}")

    except Exception as exc:
        db.rollback()
        print(f"Seeding error: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
