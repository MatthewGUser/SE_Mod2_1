from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Float
from datetime import date, datetime
from typing import List
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(db.String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(200), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(150), unique=True, nullable=False)

    # Update relationship to include cascade
    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"  # This ensures tickets are deleted with the user
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)

    # Add relationship to service tickets
    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        secondary=mechanic_service_tickets,
        back_populates="mechanics"
    )

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

    id: Mapped[int] = mapped_column(primary_key=True)
    VIN: Mapped[str] = mapped_column(db.String(17), nullable=False)
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    service_date: Mapped[datetime] = mapped_column(db.Date, nullable=False)
    user_id: Mapped[int] = mapped_column(db.Integer, ForeignKey('users.id'))

    # Relationships
    user = relationship("User", back_populates="service_tickets")
    mechanics = relationship("Mechanic", secondary=mechanic_service_tickets, back_populates="service_tickets")
    parts = relationship("Inventory", secondary=ticket_parts, back_populates="service_tickets")