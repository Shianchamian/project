import sqlite3
import numpy as np
import os

DB_PATH = "database.db"


def init_db():
    """Create the database and the 'faces' table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            relation TEXT,
            image_path TEXT NOT NULL,
            features BLOB NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_face_data(name, relation, image_path, features):
    """Save a new face record in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO faces (name, relation, image_path, features)
        VALUES (?, ?, ?, ?)
    """, (name, relation, image_path, features.tobytes()))
    conn.commit()
    conn.close()


def manage_face():
    """Retrieve all face records from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, relation, image_path FROM faces")
    faces = cursor.fetchall()  # Get all stored face records
    conn.close()
    return faces  # Return a list of face records


def delete_face(face_id):
    """删除指定ID的face记录及其关联图片"""
    # 先获取face记录信息
    face = get_face_by_id(face_id)
    
    # 如果找到记录且存在图片路径，则删除图片
    if face and face['image_path']:
        try:
            if os.path.exists(face['image_path']):
                os.remove(face['image_path'])
        except Exception as e:
            print(f"删除图片文件时出错: {e}")
    
    # 删除数据库记录
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faces WHERE id=?", (face_id,))
    conn.commit()
    conn.close()


def update_face(face_id, new_name, new_relation):
    """Update the name and relation of a face record."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE faces SET name=?, relation=? WHERE id=?", (new_name, new_relation, face_id))
    conn.commit()
    conn.close()


def add_test_data():
    """Insert sample face data into the database for testing."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add 3 sample face records
    cursor.executemany("""
        INSERT INTO faces (name, relation, image_path, features) 
        VALUES (?, ?, ?, ?)
    """, [
        ("Alice", "Friend", "assets/alice.png", b'\x00' * 512),
        ("Bob", "Brother", "assets/bob.png", b'\x00' * 512),
        ("Charlie", "Colleague", "assets/charlie.png", b'\x00' * 512)
    ])

    conn.commit()
    conn.close()


def view_database():
    """Display all records from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch all records from the database
    cursor.execute("SELECT * FROM faces")
    rows = cursor.fetchall()

    conn.close()

    # Print data if available
    if not rows:
        print("No data found in the database.")
    else:
        for row in rows:
            print(row)  # Display each record


def get_face_by_id(face_id):
    """获取指定ID的face记录详细信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, relation, image_path, features FROM faces WHERE id=?", (face_id,))
    face = cursor.fetchone()
    conn.close()
    
    if face:
        return {
            'id': face[0],
            'name': face[1],
            'relation': face[2],
            'image_path': face[3],
            'features': face[4]
        }
    return None


#Initialize the database
init_db()

# View all stored data
view_database()
