import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


class ChatDatabase:
    def __init__(self, db_path: str = "chat_database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Chat Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                customer_name TEXT,
                registration_number TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)

        # Chat Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
            )
        """)

        # Cases Table - Main case information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                case_type TEXT CHECK(case_type IN ('AC', 'RA', 'OTHER')),
                registration_number TEXT,
                customer_name TEXT,
                description TEXT,
                location TEXT,
                final_destination TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
            )
        """)

        # Case Images Table - Store uploaded images
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                session_id TEXT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                image_type TEXT,
                analysis_data TEXT,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (id),
                FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
            )
        """)

        # Case Analysis Table - Inferred data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                possible_vehicle_malfunction TEXT,
                possible_problem_resolution TEXT,
                recommended_auto_repair_shop TEXT,
                is_destination_within_prefecture BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)

        # Case Flags Table - Critical decisions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                delay_voucher_used BOOLEAN DEFAULT FALSE,
                geolocation_link_sent BOOLEAN DEFAULT FALSE,
                sworn_declaration_needed BOOLEAN DEFAULT FALSE,
                is_fast_track BOOLEAN DEFAULT FALSE,
                is_fraud BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)

        # Case Summary Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                communication_quality TEXT,
                tags TEXT,
                short_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)

        conn.commit()
        conn.close()

    def create_chat_session(
        self, customer_name: str = None, registration_number: str = None
    ) -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO chat_sessions (session_id, customer_name, registration_number)
            VALUES (?, ?, ?)
        """,
            (session_id, customer_name, registration_number),
        )

        conn.commit()
        conn.close()
        return session_id

    def add_message(self, session_id: str, sender: str, message: str):
        """Add a message to the chat session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO chat_messages (session_id, sender, message)
            VALUES (?, ?, ?)
        """,
            (session_id, sender, message),
        )

        conn.commit()
        conn.close()

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a chat session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT sender, message, timestamp
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """,
            (session_id,),
        )

        messages = []
        for row in cursor.fetchall():
            messages.append({"sender": row[0], "message": row[1], "timestamp": row[2]})

        conn.close()
        return messages

    def create_case(
        self,
        session_id: str,
        case_type: str,
        registration_number: str,
        customer_name: str,
        description: str,
        location: str,
        final_destination: str,
    ) -> int:
        """Create a new case"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO cases 
            (session_id, case_type, registration_number, customer_name, 
             description, location, final_destination)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                case_type,
                registration_number,
                customer_name,
                description,
                location,
                final_destination,
            ),
        )

        case_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return case_id

    def update_case_analysis(
        self,
        case_id: int,
        malfunction: str = None,
        resolution: str = None,
        repair_shop: str = None,
        within_prefecture: bool = None,
    ):
        """Update case analysis data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO case_analysis 
            (case_id, possible_vehicle_malfunction, possible_problem_resolution,
             recommended_auto_repair_shop, is_destination_within_prefecture)
            VALUES (?, ?, ?, ?, ?)
        """,
            (case_id, malfunction, resolution, repair_shop, within_prefecture),
        )

        conn.commit()
        conn.close()

    def update_case_flags(
        self,
        case_id: int,
        delay_voucher: bool = None,
        geolocation_sent: bool = None,
        sworn_declaration: bool = None,
        fast_track: bool = None,
        fraud: bool = None,
    ):
        """Update case flags"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO case_flags 
            (case_id, delay_voucher_used, geolocation_link_sent, 
             sworn_declaration_needed, is_fast_track, is_fraud)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                case_id,
                delay_voucher,
                geolocation_sent,
                sworn_declaration,
                fast_track,
                fraud,
            ),
        )

        conn.commit()
        conn.close()

    def update_case_summary(
        self, case_id: int, communication_quality: str, tags: List[str], summary: str
    ):
        """Update case summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tags_json = json.dumps(tags)
        cursor.execute(
            """
            INSERT OR REPLACE INTO case_summary 
            (case_id, communication_quality, tags, short_summary)
            VALUES (?, ?, ?, ?)
        """,
            (case_id, communication_quality, tags_json, summary),
        )

        conn.commit()
        conn.close()

    def get_case_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get case information by session ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                c.id, c.session_id, c.case_type, c.registration_number, c.customer_name,
                c.description, c.location, c.final_destination, c.created_at, c.updated_at,
                ca.possible_vehicle_malfunction, ca.possible_problem_resolution,
                ca.recommended_auto_repair_shop, ca.is_destination_within_prefecture,
                cf.delay_voucher_used, cf.geolocation_link_sent, cf.sworn_declaration_needed,
                cf.is_fast_track, cf.is_fraud,
                cs.communication_quality, cs.tags, cs.short_summary
            FROM cases c
            LEFT JOIN case_analysis ca ON c.id = ca.case_id
            LEFT JOIN case_flags cf ON c.id = cf.case_id
            LEFT JOIN case_summary cs ON c.id = cs.case_id
            WHERE c.session_id = ?
        """,
            (session_id,),
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # Parse tags safely
        tags = []
        if row[20]:  # cs.tags
            try:
                if isinstance(row[20], str):
                    tags = json.loads(row[20])
                else:
                    tags = []
            except (json.JSONDecodeError, TypeError):
                tags = []

        # Map the result to a dictionary
        case_data = {
            "id": row[0],
            "session_id": row[1],
            "case_type": row[2],
            "registration_number": row[3],
            "customer_name": row[4],
            "description": row[5],
            "location": row[6],
            "final_destination": row[7],
            "created_at": row[8],
            "updated_at": row[9],
            "analysis": {
                "possible_vehicle_malfunction": row[10],
                "possible_problem_resolution": row[11],
                "recommended_auto_repair_shop": row[12],
                "is_destination_within_prefecture": row[13],
            },
            "flags": {
                "delay_voucher_used": row[14],
                "geolocation_link_sent": row[15],
                "sworn_declaration_needed": row[16],
                "is_fast_track": row[17],
                "is_fraud": row[18],
            },
            "summary": {
                "communication_quality": row[19],
                "tags": tags,
                "short_summary": row[21],
            },
        }

        conn.close()
        return case_data

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all chat sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id, customer_name, registration_number, 
                   started_at, ended_at, status
            FROM chat_sessions
            ORDER BY started_at DESC
        """)

        sessions = []
        for row in cursor.fetchall():
            sessions.append(
                {
                    "session_id": row[0],
                    "customer_name": row[1],
                    "registration_number": row[2],
                    "started_at": row[3],
                    "ended_at": row[4],
                    "status": row[5],
                }
            )

        conn.close()
        return sessions

    def end_session(self, session_id: str):
        """Mark a session as ended and update related data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Begin transaction
            cursor.execute("BEGIN")

            # Update session status
            cursor.execute(
                """
                UPDATE chat_sessions 
                SET ended_at = CURRENT_TIMESTAMP, 
                    status = 'ended'
                WHERE session_id = ?
                """,
                (session_id,),
            )

            # Update case status if exists
            cursor.execute(
                """
                UPDATE cases
                SET updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (session_id,),
            )

            # Commit transaction
            conn.commit()

        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            raise e

        finally:
            conn.close()

    def update_session_info(
        self,
        session_id: str,
        customer_name: str = None,
        registration_number: str = None,
    ):
        """Update session with customer information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build dynamic update query
        update_fields = []
        values = []

        if customer_name is not None:
            update_fields.append("customer_name = ?")
            values.append(customer_name)

        if registration_number is not None:
            update_fields.append("registration_number = ?")
            values.append(registration_number)

        if update_fields:
            values.append(session_id)  # Add session_id for WHERE clause

            query = f"""
                UPDATE chat_sessions 
                SET {", ".join(update_fields)}
                WHERE session_id = ?
            """

            cursor.execute(query, values)
            conn.commit()

        conn.close()

    def update_case_info(self, session_id: str, **kwargs):
        """Update existing case information or create new case if none exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if case exists
        existing_case = self.get_case_by_session(session_id)

        if existing_case:
            # Update existing case
            case_id = existing_case["id"]

            # Build dynamic update query for cases table
            update_fields = []
            values = []

            case_fields = [
                "case_type",
                "registration_number",
                "customer_name",
                "description",
                "location",
                "final_destination",
            ]

            for field in case_fields:
                if kwargs.get(field) is not None:
                    update_fields.append(f"{field} = ?")
                    values.append(kwargs[field])

            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(case_id)

                query = f"""
                    UPDATE cases 
                    SET {", ".join(update_fields)}
                    WHERE id = ?
                """
                cursor.execute(query, values)
        else:
            # Create new case if none exists
            case_id = self.create_case(
                session_id=session_id,
                case_type=kwargs.get("case_type", "OTHER"),
                registration_number=kwargs.get("registration_number", ""),
                customer_name=kwargs.get("customer_name", ""),
                description=kwargs.get("description", ""),
                location=kwargs.get("location", ""),
                final_destination=kwargs.get("final_destination", ""),
            )

        conn.commit()
        conn.close()
        return case_id if "case_id" in locals() else None

    def store_case_image(
        self,
        session_id: str,
        filename: str,
        original_filename: str,
        image_type: str = None,
        analysis_data: dict = None,
    ):
        """Store information about an uploaded image"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get case_id if it exists
            case = self.get_case_by_session(session_id)
            case_id = case["id"] if case else None

            # Store image data
            cursor.execute(
                """
                INSERT INTO case_images (case_id, session_id, filename, original_filename, image_type, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    case_id,
                    session_id,
                    filename,
                    original_filename,
                    image_type,
                    json.dumps(analysis_data) if analysis_data else None,
                ),
            )

            image_id = cursor.lastrowid
            conn.commit()
            return image_id
        finally:
            conn.close()

    def get_case_images(
        self, session_id: str = None, case_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get all images for a case by session_id or case_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if session_id:
                cursor.execute(
                    """
                    SELECT id, filename, original_filename, image_type, analysis_data, upload_timestamp
                    FROM case_images
                    WHERE session_id = ?
                    ORDER BY upload_timestamp DESC
                """,
                    (session_id,),
                )
            elif case_id:
                cursor.execute(
                    """
                    SELECT id, filename, original_filename, image_type, analysis_data, upload_timestamp
                    FROM case_images
                    WHERE case_id = ?
                    ORDER BY upload_timestamp DESC
                """,
                    (case_id,),
                )
            else:
                return []

            images = []
            for row in cursor.fetchall():
                image = {
                    "id": row[0],
                    "filename": row[1],
                    "original_filename": row[2],
                    "image_type": row[3],
                    "analysis_data": json.loads(row[4]) if row[4] else None,
                    "upload_timestamp": row[5],
                }
                images.append(image)

            return images
        finally:
            conn.close()
