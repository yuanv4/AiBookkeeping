"""Database base configuration and utilities.

This module contains the SQLAlchemy database instance and base model class.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import Dict, Any

# SQLAlchemy database instance
db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model class with common fields and methods."""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def save(self) -> None:
        """Save the model instance to the database."""
        db.session.add(self)
        db.session.commit()

    def delete(self) -> None:
        """Delete the model instance from the database."""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs: Any) -> None:
        """Update the model instance with provided keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    @classmethod
    def get_by_id(cls, id: int):
        """Get model instance by ID."""
        return cls.query.get(id)

    @classmethod
    def get_all(cls):
        """Get all model instances."""
        return cls.query.all()

    @classmethod
    def create(cls, **kwargs: Any):
        """Create a new model instance."""
        instance = cls(**kwargs)
        instance.save()
        return instance

    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f'<{self.__class__.__name__}(id={self.id})>'