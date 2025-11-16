"""Integration tests for SQLAlchemy ORM support."""

import pytest


# Skip if SQLAlchemy not installed
pytest.importorskip("sqlalchemy")

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from toonverter import decode
from toonverter.integrations.sqlalchemy_integration import (
    bulk_query_to_toon,
    query_to_toon,
    sqlalchemy_to_toon,
)


Base = declarative_base()


class User(Base):
    """Test User model."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    age = Column(Integer)
    active = Column(Boolean, default=True)


class Post(Base):
    """Test Post model."""

    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref="posts")


class TestSQLAlchemyModelSerialization:
    """Test SQLAlchemy model serialization."""

    def setup_method(self):
        """Set up test database."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def teardown_method(self):
        """Tear down test database."""
        self.session.close()

    def test_simple_model_to_toon(self):
        """Test converting model instance to TOON."""
        user = User(id=1, name="Alice", age=30, active=True)
        self.session.add(user)
        self.session.commit()

        toon = sqlalchemy_to_toon(user)

        assert "Alice" in toon
        assert "30" in toon
        assert "true" in toon

    def test_model_roundtrip(self):
        """Test model roundtrip."""
        user_original = User(id=1, name="Bob", age=25, active=False)

        toon = sqlalchemy_to_toon(user_original)
        user_dict = decode(toon)

        assert user_dict["name"] == "Bob"
        assert user_dict["age"] == 25
        assert user_dict["active"] is False

    def test_query_result_to_toon(self):
        """Test converting query results to TOON."""
        self.session.add_all(
            [
                User(id=1, name="Alice", age=30),
                User(id=2, name="Bob", age=25),
                User(id=3, name="Carol", age=35),
            ]
        )
        self.session.commit()

        users = self.session.query(User).all()
        toon = sqlalchemy_to_toon(users)

        # Should use tabular format
        assert "[3]{" in toon
        assert "Alice" in toon
        assert "Bob" in toon
        assert "Carol" in toon

    def test_query_to_toon(self):
        """Test bulk export."""
        self.session.add_all([User(id=i, name=f"User{i}", age=20 + i) for i in range(100)])
        self.session.commit()

        toon = query_to_toon(self.session, User)

        assert "[100]{" in toon

    def test_relationships(self):
        """Test handling relationships."""
        user = User(id=1, name="Alice", age=30)
        post1 = Post(id=1, title="First Post", user=user)
        post2 = Post(id=2, title="Second Post", user=user)

        self.session.add_all([user, post1, post2])
        self.session.commit()

        toon = sqlalchemy_to_toon(user, include_relationships=True)

        assert "Alice" in toon
        assert "First Post" in toon or "posts" in toon


class TestSQLAlchemyBulkOperations:
    """Test bulk operations with SQLAlchemy."""

    def setup_method(self):
        """Set up test database."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def teardown_method(self):
        """Tear down test database."""
        self.session.close()

    def test_bulk_query_to_toon(self):
        """Test bulk import from TOON."""
        toon = """users[3]{name,age}:
  Alice,30
  Bob,25
  Carol,35"""

        bulk_query_to_toon(self.session, User, toon)

        users = self.session.query(User).all()
        assert len(users) == 3
        assert users[0].name == "Alice"

    def test_schema_export(self):
        """Test schema export to TOON."""
        schema = Base.metadata.tables["users"]
        toon = sqlalchemy_to_toon(schema, as_schema=True)

        assert "name" in toon
        assert "age" in toon
        assert "String" in toon or "Integer" in toon
