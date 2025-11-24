"""SQLAlchemy Integration Example.

Demonstrates all features of toonverter's SQLAlchemy integration:
1. ORM model serialization
2. Query result conversion
3. Schema export
4. Bulk operations

Install dependencies:
    pip install toonverter[sqlalchemy]
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, select
from sqlalchemy.orm import declarative_base, relationship, Session

from toonverter.integrations.sqlalchemy import (
    sqlalchemy_to_toon,
    toon_to_sqlalchemy,
    query_to_toon,
    bulk_query_to_toon,
    schema_to_toon,
    table_to_toon,
    bulk_insert_from_toon,
    export_table_to_toon,
)

# =============================================================================
# SETUP: Create example models
# =============================================================================

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    posts = relationship("Post", back_populates="author")

    def __repr__(self):
        return f"<User(name='{self.name}', email='{self.email}')>"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(String(5000))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    author = relationship("User", back_populates="posts")

    def __repr__(self):
        return f"<Post(title='{self.title}')>"


# =============================================================================
# 1. ORM MODEL SERIALIZATION
# =============================================================================


def example_orm_serialization():
    """Example: Convert ORM models to/from TOON."""
    print("\n" + "=" * 70)
    print("1. ORM MODEL SERIALIZATION")
    print("=" * 70)

    # Create engine and session
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)

    # Create a user
    user = User(name="Alice Johnson", email="alice@example.com", age=30)
    session.add(user)
    session.commit()

    # Convert to TOON
    print("\n📤 Model → TOON:")
    toon = sqlalchemy_to_toon(user)
    print(toon)

    # Create posts for the user
    post1 = Post(title="First Post", content="Hello World!", user_id=user.id)
    post2 = Post(title="Second Post", content="TOON is awesome", user_id=user.id)
    session.add_all([post1, post2])
    session.commit()

    # Convert with relationships
    print("\n📤 Model → TOON (with relationships):")
    session.refresh(user)  # Load relationships
    toon_with_rel = sqlalchemy_to_toon(user, include_relationships=True)
    print(toon_with_rel)

    # Convert TOON back to model
    print("\n📥 TOON → Model:")
    toon_data = """
name: Bob Smith
email: bob@example.com
age: 25
"""
    new_user = toon_to_sqlalchemy(toon_data, User)
    print(f"Created: {new_user}")
    print(f"  Name: {new_user.name}")
    print(f"  Email: {new_user.email}")
    print(f"  Age: {new_user.age}")

    session.close()


# =============================================================================
# 2. QUERY RESULT CONVERSION
# =============================================================================


def example_query_conversion():
    """Example: Convert query results to TOON."""
    print("\n" + "=" * 70)
    print("2. QUERY RESULT CONVERSION")
    print("=" * 70)

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)

    # Insert sample data
    users = [
        User(name="Alice", email="alice@example.com", age=30),
        User(name="Bob", email="bob@example.com", age=25),
        User(name="Carol", email="carol@example.com", age=35),
    ]
    session.add_all(users)
    session.commit()

    # Query all users
    print("\n📊 Query → TOON (all users):")
    result = session.execute(select(User)).scalars().all()
    toon = query_to_toon(result)
    print(toon)

    # Query specific columns
    print("\n📊 Query → TOON (name and age only):")
    result = session.execute(select(User.name, User.age))
    toon = query_to_toon(result)
    print(toon)

    # Streaming for large datasets
    print("\n📊 Bulk Query → TOON (streaming):")
    result = session.execute(select(User)).scalars().all()
    for i, chunk_toon in enumerate(bulk_query_to_toon(result, chunk_size=2)):
        print(f"\nChunk {i + 1}:")
        print(chunk_toon)

    session.close()


# =============================================================================
# 3. SCHEMA EXPORT
# =============================================================================


def example_schema_export():
    """Example: Export database schema to TOON."""
    print("\n" + "=" * 70)
    print("3. SCHEMA EXPORT")
    print("=" * 70)

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    # Export entire schema
    print("\n🗂️ Full Schema → TOON:")
    schema_toon = schema_to_toon(Base.metadata)
    print(schema_toon[:500] + "...\n(truncated)")  # Show first 500 chars

    # Export single table
    print("\n🗂️ Single Table → TOON:")
    user_table = User.__table__
    table_toon = table_to_toon(user_table)
    print(table_toon)


# =============================================================================
# 4. BULK OPERATIONS
# =============================================================================


def example_bulk_operations():
    """Example: Bulk insert and export."""
    print("\n" + "=" * 70)
    print("4. BULK OPERATIONS")
    print("=" * 70)

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)

    # Bulk insert from TOON
    print("\n📥 Bulk Insert from TOON:")
    toon_data = """
[5]{name,email,age}:
  Alice,alice@example.com,30
  Bob,bob@example.com,25
  Carol,carol@example.com,35
  Dave,dave@example.com,28
  Eve,eve@example.com,32
"""

    count = bulk_insert_from_toon(toon_data, User, session)
    print(f"✅ Inserted {count} users")

    # Verify insertion
    users = session.execute(select(User)).scalars().all()
    print(f"✅ Total users in database: {len(users)}")

    # Export table to TOON
    print("\n📤 Export Table → TOON:")
    exported_toon = export_table_to_toon("users", session)
    print(exported_toon)

    # Streaming export for large tables
    print("\n📤 Export Table → TOON (streaming):")
    for i, chunk in enumerate(export_table_to_toon("users", session, stream=True, chunk_size=2)):
        print(f"\nChunk {i + 1}:")
        print(chunk)

    session.close()


# =============================================================================
# TOKEN SAVINGS ANALYSIS
# =============================================================================


def example_token_savings():
    """Example: Compare token usage with JSON."""
    print("\n" + "=" * 70)
    print("5. TOKEN SAVINGS ANALYSIS")
    print("=" * 70)

    import json
    from toonverter.analysis import count_tokens

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)

    # Create sample data
    users = [User(name=f"User{i}", email=f"user{i}@example.com", age=20 + i) for i in range(10)]
    session.add_all(users)
    session.commit()

    # Get query result
    result = session.execute(select(User)).scalars().all()

    # Convert to TOON
    toon = query_to_toon(result)

    # Convert to JSON for comparison
    data = [{"name": u.name, "email": u.email, "age": u.age} for u in result]
    json_str = json.dumps(data, indent=2)

    # Count tokens
    toon_tokens = count_tokens(toon)
    json_tokens = count_tokens(json_str)

    print(f"\n📊 Format Comparison:")
    print(f"  JSON tokens: {json_tokens}")
    print(f"  TOON tokens: {toon_tokens}")
    print(
        f"  Savings: {json_tokens - toon_tokens} tokens ({((json_tokens - toon_tokens) / json_tokens * 100):.1f}%)"
    )

    print(f"\n📏 Size Comparison:")
    print(f"  JSON size: {len(json_str)} bytes")
    print(f"  TOON size: {len(toon)} bytes")
    print(
        f"  Savings: {len(json_str) - len(toon)} bytes ({((len(json_str) - len(toon)) / len(json_str) * 100):.1f}%)"
    )

    session.close()


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Run all examples."""
    print("\n" + "🚀 " + "=" * 66 + " 🚀")
    print("  TOONVERTER - SQLALCHEMY INTEGRATION EXAMPLES")
    print("🚀 " + "=" * 66 + " 🚀")

    example_orm_serialization()
    example_query_conversion()
    example_schema_export()
    example_bulk_operations()
    example_token_savings()

    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
