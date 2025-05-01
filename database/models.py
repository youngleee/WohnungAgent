from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
import os
import logging

Base = declarative_base()

class Listing(Base):
    __tablename__ = 'listings'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    rooms = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    district = Column(String, nullable=True)  # District/neighborhood within location
    url = Column(String, nullable=False, unique=True)
    contact_email = Column(String, nullable=True)
    has_form = Column(Boolean, default=False)
    has_balcony = Column(Boolean, default=False)
    has_garden = Column(Boolean, default=False)
    has_elevator = Column(Boolean, default=False)
    is_furnished = Column(Boolean, default=False)
    pets_allowed = Column(Boolean, default=False)
    is_wg = Column(Boolean, default=False)
    available_from = Column(String, nullable=True)  # Available from date
    floor = Column(String, nullable=True)  # Floor level
    image_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    source = Column(String, nullable=False)  # Website source
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    applications = relationship("Application", back_populates="listing", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Listing(title='{self.title}', price={self.price}, location='{self.location}')>"


class Application(Base):
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'), nullable=False)
    status = Column(String, default='pending')  # pending, success, failed
    method = Column(String, nullable=False)  # email, form
    application_date = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(String, nullable=True)
    
    listing = relationship("Listing", back_populates="applications")
    
    def __repr__(self):
        return f"<Application(listing_id={self.listing_id}, status='{self.status}', method='{self.method}')>"


def init_db(db_path='sqlite:///database/wohnungagent.db'):
    """Initialize the database and create tables if they don't exist"""
    logger = logging.getLogger(__name__)
    
    # Make sure database directory exists
    try:
        db_dir = os.path.dirname(db_path.replace('sqlite:///', ''))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory at {db_dir}")
    except Exception as e:
        logger.error(f"Error creating database directory: {e}")
    
    try:
        engine = create_engine(db_path)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        # Create a fallback in-memory database if file-based DB fails
        try:
            memory_engine = create_engine('sqlite:///:memory:')
            Base.metadata.create_all(memory_engine)
            Memory_Session = sessionmaker(bind=memory_engine)
            logger.warning("Using in-memory database as fallback")
            return Memory_Session()
        except Exception as e2:
            logger.critical(f"Fatal error creating even memory database: {e2}")
            raise


def get_session(db_path='sqlite:///database/wohnungagent.db'):
    """Get a database session"""
    engine = create_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session() 