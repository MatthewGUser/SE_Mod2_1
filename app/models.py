from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Float
from datetime import date, datetime
from typing import List
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_jwt_extended import create_access_token

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=False)  # Remove unique constraint
    is_admin = db.Column(db.Boolean, default=False)

    # Update relationship to include cascade
    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"  # This ensures tickets are deleted with the user
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_token(self):
        """Generate JWT token for user"""
        return create_access_token(
            identity=str(self.id),
            additional_claims={
                'is_admin': bool(self.is_admin)
            }
        )

    def to_dict(self):
        """Convert user to dictionary with role information"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'service_tickets': [ticket.to_dict() for ticket in self.service_tickets]
        }

# Junction table for mechanics and service tickets
mechanic_service_tickets = Table(
    'mechanic_service_tickets',
    db.Model.metadata,
    db.Column('mechanic_id', db.Integer, ForeignKey('mechanics.id'), primary_key=True),
    db.Column('ticket_id', db.Integer, ForeignKey('service_tickets.id'), primary_key=True)
)

class Mechanic(db.Model):
    __tablename__ = 'mechanics'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    specialty: Mapped[str] = mapped_column(db.String(100))
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    
    # Relationships
    service_tickets = relationship('ServiceTicket', secondary='mechanic_service_tickets',
                                 back_populates='mechanics')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty,
            'phone': self.phone
        }

    def __repr__(self):
        return f'<Mechanic {self.name}>'

# Junction table for Inventory and ServiceTicket
ticket_parts = Table(
    'ticket_parts',
    db.Model.metadata,
    db.Column('ticket_id', db.Integer, ForeignKey('service_tickets.id'), primary_key=True),
    db.Column('part_id', db.Integer, ForeignKey('inventory.id'), primary_key=True)
)

class Inventory(db.Model):
    """Model for tracking parts inventory"""
    __tablename__ = 'inventory'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        secondary=ticket_parts,
        back_populates="parts"
    )

    def __repr__(self):
        return f'<Part {self.name} - ${self.price}>'

class ServiceTicket(db.Model):
    __tablename__ = 'service_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="service_tickets")
    mechanics = relationship("Mechanic", secondary=mechanic_service_tickets, back_populates="service_tickets")
    parts = relationship("Inventory", secondary=ticket_parts, back_populates="service_tickets")

class Part(db.Model):
    __tablename__ = 'parts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    part_number = db.Column(db.String(50), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'part_number': self.part_number,
            'price': float(self.price),
            'quantity': self.quantity
        }