import sqlite3
import hashlib
import secrets
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from config import BASE_DIR

DB_PATH = BASE_DIR / "scholarai.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT,
            nationality TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # User Profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            bachelor_field TEXT,
            gpa REAL,
            gpa_scale REAL,
            target_degree_field TEXT,
            target_countries TEXT,
            work_experience_years REAL,
            english_test TEXT,
            funding_type_needed TEXT,
            research_experience TEXT,
            additional_notes TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Bookmarks / Saved scholarships table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scholarship_id TEXT NOT NULL,
            saved_at TEXT NOT NULL,
            UNIQUE(user_id, scholarship_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

# Password hashing utilities
def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    hashed = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100_000).hex()
    return hashed, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    hashed, _ = hash_password(password, salt)
    return secrets.compare_digest(hashed, stored_hash)

# Authentication & User Service
class UserService:

    @staticmethod
    def register_user(email: str, password: str, full_name: str, nationality: str) -> Dict[str, Any]:
        email = email.strip().lower()
        if not email or "@" not in email:
            raise ValueError("Please provide a valid email address.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        
        pwd_hash, salt = hash_password(password)
        now = datetime.utcnow().isoformat()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash, salt, full_name, nationality, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (email, pwd_hash, salt, full_name.strip(), nationality.strip(), now)
            )
            user_id = cursor.lastrowid

            # Create initial default profile
            cursor.execute("""
                INSERT INTO user_profiles (
                    user_id, bachelor_field, gpa, gpa_scale, target_degree_field,
                    target_countries, work_experience_years, english_test,
                    funding_type_needed, research_experience, additional_notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, "", 3.5, 4.0, "", json.dumps([]), 1.0, "", "Fully Funded", "", "", now
            ))

            conn.commit()

            # Create session token
            token = UserService._create_session(user_id, conn)
            
            return {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "nationality": nationality,
                "token": token
            }
        except sqlite3.IntegrityError:
            raise ValueError("An account with this email address already exists.")
        finally:
            conn.close()

    @staticmethod
    def login_user(email: str, password: str) -> Dict[str, Any]:
        email = email.strip().lower()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, email, password_hash, salt, full_name, nationality FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise ValueError("Invalid email or password.")

        if not verify_password(password, row["password_hash"], row["salt"]):
            conn.close()
            raise ValueError("Invalid email or password.")

        user_id = row["id"]
        token = UserService._create_session(user_id, conn)
        conn.close()

        return {
            "id": user_id,
            "email": row["email"],
            "full_name": row["full_name"],
            "nationality": row["nationality"],
            "token": token
        }

    @staticmethod
    def _create_session(user_id: int, conn: sqlite3.Connection) -> str:
        token = secrets.token_hex(32)
        now = datetime.utcnow()
        expires = (now + timedelta(days=30)).isoformat()
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now.isoformat(), expires)
        )
        conn.commit()
        return token

    @staticmethod
    def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id, u.email, u.full_name, u.nationality, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (token,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None
        
        # Check expiration
        expires = datetime.fromisoformat(row["expires_at"])
        if datetime.utcnow() > expires:
            return None

        return {
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "nationality": row["nationality"]
        }

    @staticmethod
    def logout(token: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def save_profile(user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        # Update user's full_name and nationality in users table if present
        if profile_data.get("full_name") or profile_data.get("nationality"):
            cursor.execute(
                "UPDATE users SET full_name = COALESCE(?, full_name), nationality = COALESCE(?, nationality) WHERE id = ?",
                (profile_data.get("full_name"), profile_data.get("nationality"), user_id)
            )

        countries_json = json.dumps(profile_data.get("target_countries", []))

        cursor.execute("""
            INSERT INTO user_profiles (
                user_id, bachelor_field, gpa, gpa_scale, target_degree_field,
                target_countries, work_experience_years, english_test,
                funding_type_needed, research_experience, additional_notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                bachelor_field = excluded.bachelor_field,
                gpa = excluded.gpa,
                gpa_scale = excluded.gpa_scale,
                target_degree_field = excluded.target_degree_field,
                target_countries = excluded.target_countries,
                work_experience_years = excluded.work_experience_years,
                english_test = excluded.english_test,
                funding_type_needed = excluded.funding_type_needed,
                research_experience = excluded.research_experience,
                additional_notes = excluded.additional_notes,
                updated_at = excluded.updated_at
        """, (
            user_id,
            profile_data.get("bachelor_field", ""),
            profile_data.get("gpa", 3.5),
            profile_data.get("gpa_scale", 4.0),
            profile_data.get("target_degree_field", ""),
            countries_json,
            profile_data.get("work_experience_years", 1.0),
            profile_data.get("english_test", ""),
            profile_data.get("funding_type_needed", "Fully Funded"),
            profile_data.get("research_experience", ""),
            profile_data.get("additional_notes", ""),
            now
        ))

        conn.commit()
        conn.close()
        return {"success": True, "updated_at": now}

    @staticmethod
    def get_profile(user_id: int) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.full_name, u.nationality, u.email,
                   p.bachelor_field, p.gpa, p.gpa_scale, p.target_degree_field,
                   p.target_countries, p.work_experience_years, p.english_test,
                   p.funding_type_needed, p.research_experience, p.additional_notes, p.updated_at
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = ?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        countries = []
        if row["target_countries"]:
            try:
                countries = json.loads(row["target_countries"])
            except Exception:
                countries = []

        return {
            "full_name": row["full_name"],
            "nationality": row["nationality"],
            "email": row["email"],
            "bachelor_field": row["bachelor_field"] or "",
            "gpa": row["gpa"] if row["gpa"] is not None else 3.5,
            "gpa_scale": row["gpa_scale"] if row["gpa_scale"] is not None else 4.0,
            "target_degree_field": row["target_degree_field"] or "",
            "target_countries": countries,
            "work_experience_years": row["work_experience_years"] if row["work_experience_years"] is not None else 0.0,
            "english_test": row["english_test"] or "",
            "funding_type_needed": row["funding_type_needed"] or "Fully Funded",
            "research_experience": row["research_experience"] or "",
            "additional_notes": row["additional_notes"] or ""
        }

    @staticmethod
    def toggle_bookmark(user_id: int, scholarship_id: str) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM bookmarks WHERE user_id = ? AND scholarship_id = ?", (user_id, scholarship_id))
        exists = cursor.fetchone()

        if exists:
            cursor.execute("DELETE FROM bookmarks WHERE user_id = ? AND scholarship_id = ?", (user_id, scholarship_id))
            conn.commit()
            conn.close()
            return {"bookmarked": False, "scholarship_id": scholarship_id}
        else:
            now = datetime.utcnow().isoformat()
            cursor.execute("INSERT INTO bookmarks (user_id, scholarship_id, saved_at) VALUES (?, ?, ?)", (user_id, scholarship_id, now))
            conn.commit()
            conn.close()
            return {"bookmarked": True, "scholarship_id": scholarship_id}

    @staticmethod
    def get_bookmarks(user_id: int) -> List[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT scholarship_id FROM bookmarks WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [r["scholarship_id"] for r in rows]

# Initialize database tables on import
init_db()
