# models.py - Database Models for User History
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for storing user information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with translations
    translations = db.relationship('Translation', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'total_translations': len(self.translations)
        }

class Translation(db.Model):
    """Translation model for storing translation history"""
    __tablename__ = 'translations'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Optional user
    
    # Image information
    original_filename = db.Column(db.String(255), nullable=False)
    image_size = db.Column(db.Integer, nullable=False)  # File size in bytes
    image_dimensions = db.Column(db.String(50), nullable=True)  # "width x height"
    
    # Translation data
    original_texts = db.Column(db.Text, nullable=False)  # JSON string of original texts
    translated_texts = db.Column(db.Text, nullable=False)  # JSON string of translated texts
    detected_language = db.Column(db.String(10), nullable=True)  # Language code
    confidence_scores = db.Column(db.Text, nullable=True)  # JSON string of OCR confidence scores
    
    # Processing metadata
    processing_time = db.Column(db.Float, nullable=True)  # Time taken in seconds
    ocr_engine = db.Column(db.String(50), default='tesseract')
    translation_engine = db.Column(db.String(50), default='google_translate')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Translation {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'image_size': self.image_size,
            'image_dimensions': self.image_dimensions,
            'original_texts': json.loads(self.original_texts) if self.original_texts else [],
            'translated_texts': json.loads(self.translated_texts) if self.translated_texts else [],
            'detected_language': self.detected_language,
            'confidence_scores': json.loads(self.confidence_scores) if self.confidence_scores else [],
            'processing_time': self.processing_time,
            'ocr_engine': self.ocr_engine,
            'translation_engine': self.translation_engine,
            'created_at': self.created_at.isoformat()
        }
    
    @staticmethod
    def create_from_result(filename, file_size, dimensions, original_texts, translated_texts, 
                          confidence_scores=None, processing_time=None, user_id=None, session_id=None):
        """Create a Translation record from processing results"""
        translation = Translation(
            session_id=session_id or str(uuid.uuid4()),
            user_id=user_id,
            original_filename=filename,
            image_size=file_size,
            image_dimensions=dimensions,
            original_texts=json.dumps(original_texts),
            translated_texts=json.dumps(translated_texts),
            confidence_scores=json.dumps(confidence_scores) if confidence_scores else None,
            processing_time=processing_time
        )
        return translation

class UserSession(db.Model):
    """User session model for tracking anonymous users"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }