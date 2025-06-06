"""Database base configuration and utilities.

This module contains the SQLAlchemy database instance and base model class.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# SQLAlchemy database instance
db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model class with common fields and methods."""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """Save the model instance to the database."""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        """Delete the model instance from the database."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update(self, **kwargs):
        """Update the model instance with provided keyword arguments."""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    @classmethod
    def get_by_id(cls, id):
        """Get model instance by ID."""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """Get all model instances."""
        return cls.query.all()
    
    @classmethod
    def create(cls, **kwargs):
        """Create a new model instance."""
        instance = cls(**kwargs)
        instance.save()
        return instance
    
    def __repr__(self):
        return f'<{self.__class__.__name__}(id={self.id})>'