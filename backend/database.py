"""
Database module for voice authentication system.
Handles user creation, voice embeddings storage, and OTP management.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# Database path
DATABASE_DIR = Path(__file__).parent.parent / "database"
DATABASE_PATH = DATABASE_DIR / "database.db"

# Ensure database directory exists
DATABASE_DIR.mkdir(exist_ok=True)


class Database:
    """SQLite database handler for voice authentication system."""
    
    def __init__(self, db_path: str = str(DATABASE_PATH)):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                voice_embedding TEXT,
                voice_sample_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # OTP table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp (
                otp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                otp_code TEXT NOT NULL,
                expiry_time INTEGER,
                verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Login attempts table (for tracking suspicious activity)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                similarity_score REAL,
                spoof_probability REAL,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def create_user(self, name: str, email: str, password_hash: str) -> int:
        """
        Create a new user.
        
        Args:
            name: User's full name
            email: User's email
            password_hash: Hashed password
            
        Returns:
            User ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            ''', (name, email, password_hash))
            
            conn.commit()
            user_id = cursor.lastrowid
            logger.info(f"User created: {email}")
            return user_id
        except sqlite3.IntegrityError as e:
            logger.error(f"User creation failed: {e}")
            raise ValueError(f"Email already exists")
        finally:
            conn.close()
    
    def get_user_by_email(self, email: str):
        """Get user by email."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        return user
    
    def get_user_by_id(self, user_id: int):
        """Get user by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return user
    
    def save_voice_embedding(self, user_id: int, embedding: list, voice_sample_path: str):
        """
        Save voice embedding for user.
        
        Args:
            user_id: User ID
            embedding: Voice embedding as list
            voice_sample_path: Path to stored audio file
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        embedding_json = json.dumps(embedding)
        logger.info(f"[DB] Saving embedding for user {user_id}: length={len(embedding)}, json_size={len(embedding_json)} bytes")
        
        cursor.execute('''
            UPDATE users 
            SET voice_embedding = ?, voice_sample_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (embedding_json, voice_sample_path, user_id))
        
        conn.commit()
        conn.close()
        logger.info(f"[DB] ✓ Voice embedding saved for user {user_id}")
    
    def get_voice_embedding(self, user_id: int) -> list or None:
        """Get voice embedding for user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT voice_embedding FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            embedding = json.loads(result[0])
            logger.info(f"[DB] Retrieved embedding for user {user_id}: length={len(embedding)}")
            return embedding
        else:
            logger.warning(f"[DB] No embedding found for user {user_id}")
            return None
    
    def save_otp(self, user_id: int, otp_code: str, expiry_time: int) -> int:
        """
        Save OTP for user.
        
        Args:
            user_id: User ID
            otp_code: 6-digit OTP code
            expiry_time: Expiration time in seconds
            
        Returns:
            OTP ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO otp (user_id, otp_code, expiry_time)
            VALUES (?, ?, ?)
        ''', (user_id, otp_code, expiry_time))
        
        conn.commit()
        otp_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"OTP saved for user {user_id}")
        return otp_id
    
    def verify_otp(self, user_id: int, otp_code: str) -> bool:
        """
        Verify OTP for user.
        
        Args:
            user_id: User ID
            otp_code: OTP code to verify
            
        Returns:
            True if OTP is valid, False otherwise
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get the most recent OTP for user
        cursor.execute('''
            SELECT otp_id, otp_code, created_at, expiry_time 
            FROM otp 
            WHERE user_id = ? AND verified = 0
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (user_id,))
        
        otp_record = cursor.fetchone()
        conn.close()
        
        if not otp_record:
            return False
        
        # Check if OTP matches
        if otp_record['otp_code'] != otp_code:
            return False
        
        # Check if OTP is expired
        created_time = datetime.fromisoformat(otp_record['created_at']).timestamp()
        current_time = datetime.now().timestamp()
        
        if current_time - created_time > otp_record['expiry_time']:
            return False
        
        # Mark OTP as verified
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE otp SET verified = 1 WHERE otp_id = ?
        ''', (otp_record['otp_id'],))
        conn.commit()
        conn.close()
        
        logger.info(f"OTP verified for user {user_id}")
        return True
    
    def record_login_attempt(self, user_id: int, similarity_score: float, spoof_probability: float, status: str):
        """Record login attempt for auditing."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO login_attempts (user_id, similarity_score, spoof_probability, status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, similarity_score, spoof_probability, status))
        
        conn.commit()
        conn.close()


# Global database instance
db = Database()
