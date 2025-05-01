from .models import Listing, Application, get_session
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

def add_listing(listing_data):
    """
    Add a new listing to the database
    
    Args:
        listing_data (dict): Dictionary containing listing data
        
    Returns:
        Listing: The created listing object or None if failed
    """
    session = get_session()
    try:
        listing = Listing(**listing_data)
        session.add(listing)
        session.commit()
        return listing
    except IntegrityError:
        session.rollback()
        logger.info(f"Listing already exists: {listing_data.get('url', 'unknown')}")
        return None
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding listing: {e}")
        return None
    finally:
        session.close()


def get_listing_by_url(url):
    """
    Get a listing by its URL
    
    Args:
        url (str): The URL of the listing
        
    Returns:
        Listing: The listing object or None if not found
    """
    session = get_session()
    try:
        listing = session.query(Listing).filter(Listing.url == url).first()
        return listing
    finally:
        session.close()


def create_application(listing_id, method, status="pending", notes=None):
    """
    Create a new application record
    
    Args:
        listing_id (int): ID of the listing being applied to
        method (str): Method of application (email, form)
        status (str): Status of the application
        notes (str): Additional notes
        
    Returns:
        Application: The created application object or None if failed
    """
    session = get_session()
    try:
        application = Application(
            listing_id=listing_id,
            method=method,
            status=status,
            notes=notes
        )
        session.add(application)
        session.commit()
        return application
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating application: {e}")
        return None
    finally:
        session.close()


def update_application_status(application_id, status, notes=None):
    """
    Update the status of an application
    
    Args:
        application_id (int): ID of the application
        status (str): New status (pending, success, failed)
        notes (str): Optional notes to add
        
    Returns:
        bool: True if update successful, False otherwise
    """
    session = get_session()
    try:
        application = session.query(Application).filter(Application.id == application_id).first()
        if not application:
            return False
            
        application.status = status
        if notes:
            application.notes = notes
            
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating application status: {e}")
        return False
    finally:
        session.close()


def get_listings_with_filters(filters):
    """
    Get listings that match the given filters
    
    Args:
        filters (dict): Dictionary of filters to apply
        
    Returns:
        list: List of Listing objects that match the filters
    """
    session = get_session()
    try:
        query = session.query(Listing)
        
        # Apply filters only if the table has the necessary columns
        # Use explicit hasattr checks for each attribute and log any issues
        
        # Location and district
        if 'location' in filters and filters['location'] and hasattr(Listing, 'location'):
            try:
                query = query.filter(Listing.location.ilike(f"%{filters['location']}%"))
            except Exception as e:
                logger.error(f"Error filtering by location: {e}")
            
        if 'district' in filters and filters['district'] and hasattr(Listing, 'district'):
            try:
                query = query.filter(Listing.district.ilike(f"%{filters['district']}%"))
            except Exception as e:
                logger.error(f"Error filtering by district: {e}")
        
        # Price range
        if 'min_price' in filters and filters['min_price'] is not None and hasattr(Listing, 'price'):
            try:
                query = query.filter(Listing.price >= float(filters['min_price']))
            except Exception as e:
                logger.error(f"Error filtering by min_price: {e}")
            
        if 'max_price' in filters and filters['max_price'] is not None and hasattr(Listing, 'price'):
            try:
                query = query.filter(Listing.price <= float(filters['max_price']))
            except Exception as e:
                logger.error(f"Error filtering by max_price: {e}")
        
        # Size range
        if 'min_size' in filters and filters['min_size'] is not None and hasattr(Listing, 'size'):
            try:
                query = query.filter(Listing.size >= float(filters['min_size']))
            except Exception as e:
                logger.error(f"Error filtering by min_size: {e}")
            
        if 'max_size' in filters and filters['max_size'] is not None and hasattr(Listing, 'size'):
            try:
                query = query.filter(Listing.size <= float(filters['max_size']))
            except Exception as e:
                logger.error(f"Error filtering by max_size: {e}")
        
        # Room count
        if 'min_rooms' in filters and filters['min_rooms'] is not None and hasattr(Listing, 'rooms'):
            try:
                query = query.filter(Listing.rooms >= float(filters['min_rooms']))
            except Exception as e:
                logger.error(f"Error filtering by min_rooms: {e}")
            
        if 'max_rooms' in filters and filters['max_rooms'] is not None and hasattr(Listing, 'rooms'):
            try:
                query = query.filter(Listing.rooms <= float(filters['max_rooms']))
            except Exception as e:
                logger.error(f"Error filtering by max_rooms: {e}")
        
        # Property features
        if 'balcony' in filters and filters['balcony'] and hasattr(Listing, 'has_balcony'):
            try:
                query = query.filter(Listing.has_balcony == True)
            except Exception as e:
                logger.error(f"Error filtering by balcony: {e}")
            
        if 'garden' in filters and filters['garden'] and hasattr(Listing, 'has_garden'):
            try:
                query = query.filter(Listing.has_garden == True)
            except Exception as e:
                logger.error(f"Error filtering by garden: {e}")
            
        if 'elevator' in filters and filters['elevator'] and hasattr(Listing, 'has_elevator'):
            try:
                query = query.filter(Listing.has_elevator == True)
            except Exception as e:
                logger.error(f"Error filtering by elevator: {e}")
            
        if 'furnished' in filters and filters['furnished'] and hasattr(Listing, 'is_furnished'):
            try:
                query = query.filter(Listing.is_furnished == True)
            except Exception as e:
                logger.error(f"Error filtering by furnished: {e}")
            
        if 'pets_allowed' in filters and filters['pets_allowed'] and hasattr(Listing, 'pets_allowed'):
            try:
                query = query.filter(Listing.pets_allowed == True)
            except Exception as e:
                logger.error(f"Error filtering by pets_allowed: {e}")
            
        if 'wg' in filters and hasattr(Listing, 'is_wg'):
            try:
                # Only include WG if allowed
                if not filters['wg']:
                    query = query.filter(Listing.is_wg == False)
            except Exception as e:
                logger.error(f"Error filtering by wg: {e}")
        
        # Date and floor filters are more complex since they're strings
        # These are currently commented out to prevent errors
        # if 'move_in_date' in filters and filters['move_in_date'] and hasattr(Listing, 'available_from'):
        #     # Custom date handling here
        #     pass
        
        # if 'floor' in filters and filters['floor'] != "Beliebig" and hasattr(Listing, 'floor'):
        #     # Custom floor handling here
        #     pass
        
        try:
            return query.all()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []  # Return empty list on error
            
    except Exception as e:
        logger.error(f"Unexpected error in get_listings_with_filters: {e}")
        return []  # Return empty list on error
    finally:
        session.close()


def get_applied_listings():
    """
    Get all listings that have been applied to
    
    Returns:
        list: List of tuples (Listing, Application) that have been applied to
    """
    session = get_session()
    try:
        results = session.query(Listing, Application).join(
            Application, Listing.id == Application.listing_id
        ).all()
        return results
    finally:
        session.close()


def has_applied_to_listing(listing_id):
    """
    Check if an application has been made to a listing
    
    Args:
        listing_id (int): ID of the listing
        
    Returns:
        bool: True if an application exists, False otherwise
    """
    session = get_session()
    try:
        application = session.query(Application).filter(
            Application.listing_id == listing_id
        ).first()
        return application is not None
    finally:
        session.close() 