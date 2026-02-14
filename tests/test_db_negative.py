"""
Negative Tests for DatabaseManager.

These tests verify robustness against:
1. Corrupt database files
2. Missing schema files
3. Concurrent writes (database locking)
4. Disk full / IO errors (simulated via mocks)

This ensures the system behaves predictably (raises expected exceptions) when infrastructure fails.
"""
import unittest
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.data.db_manager import DatabaseManager
from src.core.entities.user import User

class TestDatabaseNegative(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)
        self.db_path = self.test_path / "test_negative.db"
        self.schema_path = self.test_path / "schema.sql"
        
        # Write minimal valid schema for setup
        self.schema_path.write_text("CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, created_at TEXT, height REAL, weight REAL, preferences TEXT);", encoding="utf-8")
            
    def tearDown(self):
        import gc
        gc.collect()
        try:
            self.test_dir.cleanup()
        except PermissionError:
            # Retry once after a short delay for Windows file locking issues
            time.sleep(0.2)
            try:
                self.test_dir.cleanup()
            except PermissionError:
                pass 

    def test_corrupt_database_file(self):
        """Test behavior when the database file is corrupt."""
        self.db_path.write_text("THIS IS NOT A SQLITE DATABASE FILE", encoding="utf-8")
            
        with self.assertRaises(sqlite3.DatabaseError):
            DatabaseManager(db_path=str(self.db_path), schema_path=str(self.schema_path))

    def test_missing_schema_file(self):
        """Test behavior when the schema file is missing during initialization."""
        missing_schema = self.test_path / "non_existent.sql"
        
        # We need to mock the default schema fallback check in DatabaseManager
        # DatabaseManager checks: if not os.path.exists(schema_path): try default
        # We want to fail even if default exists, OR we want to verify it fails when BOTH are missing.
        # Let's mock os.path.exists to return False for the specific file AND the fallback.
        
        # Actually, simpler: define a fallback path that DEFINITELY doesn't exist.
        # But `DatabaseManager` calculates fallback internal to `_init_db`.
        # So we must mock where `os.path.dirname(__file__)` points to, OR mock `os.path.exists` completely.
        
        with patch("src.data.db_manager.os.path.exists", return_value=False):
            with patch("builtins.open", side_effect=FileNotFoundError("Mocked missing file")):
                 with self.assertRaises(FileNotFoundError):
                    DatabaseManager(db_path=str(self.db_path), schema_path=str(missing_schema))

    def test_concurrent_writes_locking(self):
        """Test behavior when database is locked by another connection."""
        
        # 1. Initialize DB first (creates table) via separate call so the file is ready
        DatabaseManager(db_path=str(self.db_path), schema_path=str(self.schema_path))
        
        # 2. Open a connection and LOCK it
        # Note: 'timeout' default in python sqlite3 is 5.0 seconds.
        conn1 = sqlite3.connect(str(self.db_path))
        cursor1 = conn1.cursor()
        cursor1.execute("BEGIN EXCLUSIVE TRANSACTION") 
        
        # 3. Create a separate DB Manager that will try to write
        # We want it to fail FAST.
        
        timeout_val = 0.1
        original_connect = sqlite3.connect
        def connect_with_timeout(*args, **kwargs):
            if args and str(args[0]) == str(self.db_path):
                kwargs['timeout'] = timeout_val
            return original_connect(*args, **kwargs)

        try:
            with patch('sqlite3.connect', side_effect=connect_with_timeout):
                 # This should fail right here in __init__ because executescript needs a lock
                 with self.assertRaises(sqlite3.OperationalError) as cm:
                     DatabaseManager(db_path=str(self.db_path), schema_path=str(self.schema_path))
                 self.assertIn("database is locked", str(cm.exception))
                 
        finally:
            conn1.rollback()
            conn1.close()

    def test_simulated_disk_io_error(self):
        """Test handling of disk I/O errors."""
        db_manager = DatabaseManager(db_path=str(self.db_path), schema_path=str(self.schema_path))
        user = User(username="DiskFullUser")
        
        mock_conn = MagicMock()
        mock_conn.commit.side_effect = sqlite3.OperationalError("disk I/O error")
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = None 
        mock_conn.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        with patch('src.data.db_manager.sqlite3.connect', return_value=mock_conn):
            with self.assertRaises(sqlite3.OperationalError) as cm:
                db_manager.save_user(user)
            self.assertIn("disk I/O error", str(cm.exception))
            
            mock_conn.close.assert_called()

if __name__ == '__main__':
    unittest.main()
