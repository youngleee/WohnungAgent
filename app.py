import streamlit as st
import asyncio
import os
import pandas as pd
import logging
from datetime import datetime
import time
import threading
from typing import Dict, Any, List
import json
import nest_asyncio
import sys
from dotenv import load_dotenv

# Apply nest_asyncio to allow running async code in Streamlit
nest_asyncio.apply()

# Set a timeout for asyncio operations to prevent hangs
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import project modules
from database import init_db, get_applied_listings, has_applied_to_listing
from utils import SearchManager, ApplicationManager
from scrapers import WGGesuchtScraper, ImmoScoutScraper, ImmonetScraper, ImmoweltScraper

# Load environment variables (will be used as defaults)
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the database
db_session = init_db()

# Ensure required directories exist
os.makedirs("temp", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("database", exist_ok=True)

# Page configuration
st.set_page_config(
    page_title="WohnungAgent",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to load template
def load_template(template_path: str) -> str:
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as file:
            return file.read()
    return ""

# Main async function to run search
async def run_search(filters, search_sources):
    # Log the filters for debugging
    logger.info(f"Starting search with filters: {filters}")
    logger.info(f"Search sources: {search_sources}")
    
    search_manager = SearchManager(sources=search_sources)
    try:
        await search_manager.initialize_scrapers(headless=True)
        listings = await search_manager.search_all(filters)
        logger.info(f"Found {len(listings)} new listings from scrapers")
        
        all_listings = search_manager.combine_with_database(listings, filters)
        logger.info(f"Combined total: {len(all_listings)} listings after filtering")
        return all_listings
    finally:
        await search_manager.close_scrapers()

# Async function to apply to a listing
async def apply_to_listing(listing, application_data, attachments=None):
    # Determine which scraper to use based on source
    if listing['source'] == 'wg_gesucht':
        scraper = WGGesuchtScraper()
    elif listing['source'] == 'immoscout24':
        scraper = ImmoScoutScraper()
    elif listing['source'] == 'immonet':
        scraper = ImmonetScraper()
    elif listing['source'] == 'immowelt':
        scraper = ImmoweltScraper()
    else:
        return False, "Unknown source"
    
    try:
        await scraper.initialize()
        app_manager = ApplicationManager(application_data, attachments)
        success, message = await app_manager.apply_to_listing(scraper, listing)
        return success, message
    finally:
        await scraper.close()

# Store personal info in browser session
def update_session_state():
    """Updates session state with values from input widgets"""
    # Update personal data from input fields
    st.session_state.first_name = st.session_state.input_first_name
    st.session_state.last_name = st.session_state.input_last_name
    st.session_state.email = st.session_state.input_email
    st.session_state.phone = st.session_state.input_phone
    st.session_state.gender = st.session_state.input_gender
    st.session_state.occupation = st.session_state.input_occupation
    st.session_state.custom_message = st.session_state.input_custom_message
    st.session_state.saved_data = True

# Initialize session state for personal data
if 'first_name' not in st.session_state:
    st.session_state.first_name = ""
    st.session_state.last_name = ""
    st.session_state.email = ""
    st.session_state.phone = ""
    st.session_state.occupation = ""
    st.session_state.gender = "male"
    st.session_state.custom_message = ""
    st.session_state.saved_data = False

def main():
    # Title and description
    st.title("🏠 WohnungAgent")
    st.markdown("Automatische Wohnungssuche und Bewerbung auf WG-Gesucht, Immobilienscout24, Immonet und Immowelt")
    
    # Sidebar for filters and personal info
    with st.sidebar:
        # Tabs for the sidebar content
        sidebar_tab1, sidebar_tab2 = st.tabs(["Suchfilter", "Persönliche Daten"])
        
        with sidebar_tab1:
            st.header("Filter")
            
            # Location filter
            location = st.text_input("Stadt", "Berlin")
            district = st.text_input("Stadtteil (optional)", 
                                   help="Leer lassen, um in allen Stadtteilen zu suchen")
            
            # Price range
            st.subheader("Preis")
            min_price = st.number_input("Mindest-Kaltmiete (€)", min_value=0, value=0)
            max_price = st.number_input("Maximale Kaltmiete (€)", min_value=0, value=1000)
            
            # Size range
            st.subheader("Größe")
            min_size = st.number_input("Mindestgröße (m²)", min_value=0, value=30)
            max_size = st.number_input("Maximale Größe (m²)", min_value=0, value=150)
            
            # Room count
            st.subheader("Zimmeranzahl")
            min_rooms = st.number_input("Mindestanzahl Zimmer", min_value=0.0, value=1.0, step=0.5)
            max_rooms = st.number_input("Maximale Anzahl Zimmer", min_value=0.0, value=5.0, step=0.5)
            
            # Additional filters
            st.subheader("Zusätzliche Filter")
            col1, col2 = st.columns(2)
            with col1:
                balcony = st.checkbox("Balkon", value=False)
                garden = st.checkbox("Garten", value=False)
                elevator = st.checkbox("Aufzug", value=False)
            
            with col2:
                furnished = st.checkbox("Möbliert", value=False)
                pets_allowed = st.checkbox("Haustiere erlaubt", value=False)
                allow_wg = st.checkbox("WG erlaubt", value=False)
            
            # Move-in date
            st.subheader("Einzugsdatum")
            move_in_date = st.date_input("Frühestes Einzugsdatum", value=None, help="Leer lassen, wenn sofort verfügbar")
            
            # Floor
            floor_options = ["Beliebig", "Erdgeschoss", "1. bis 4. Stock", "Ab 5. Stock"]
            floor = st.selectbox("Etage", options=floor_options)
            
            # Source selection
            st.subheader("Quellen")
            col3, col4 = st.columns(2)
            with col3:
                use_wg_gesucht = st.checkbox("WG-Gesucht", value=True)
                use_immoscout = st.checkbox("Immobilienscout24", value=True)
            
            with col4:
                use_immonet = st.checkbox("Immonet", value=True)
                use_immowelt = st.checkbox("Immowelt", value=True)
        
        with sidebar_tab2:
            st.header("Persönliche Daten")
            st.info("Diese Daten werden für Formular-Bewerbungen verwendet.")
            
            # Get values from session state if they exist
            first_name = st.text_input("Vorname", value=st.session_state.first_name, 
                                     key="input_first_name", on_change=update_session_state)
                                     
            last_name = st.text_input("Nachname", value=st.session_state.last_name,
                                    key="input_last_name", on_change=update_session_state)
                                    
            email = st.text_input("E-Mail", value=st.session_state.email,
                                key="input_email", on_change=update_session_state)
                                
            phone = st.text_input("Telefon", value=st.session_state.phone,
                                key="input_phone", on_change=update_session_state)
                                
            gender = st.selectbox("Anrede", options=["male", "female"], 
                                format_func=lambda x: "Herr" if x == "male" else "Frau",
                                index=0 if st.session_state.gender == "male" else 1,
                                key="input_gender", on_change=update_session_state)
                                
            occupation = st.text_input("Beruf", value=st.session_state.occupation,
                                     key="input_occupation", on_change=update_session_state)
            
            custom_message = st.text_area("Persönliche Nachricht", 
                                        value=st.session_state.custom_message,
                                        height=100,
                                        help="Diese Nachricht wird in Bewerbungen eingefügt.",
                                        key="input_custom_message", on_change=update_session_state)
            
            # File uploads for attachments
            st.subheader("Dokumente für Bewerbungen")
            st.markdown("Dokumente werden nur für die aktuelle Sitzung gespeichert.")
            schufa = st.file_uploader("SCHUFA-Auskunft", type=["pdf"])
            income = st.file_uploader("Einkommensnachweis", type=["pdf"])
            id_doc = st.file_uploader("Personalausweis", type=["pdf", "jpg", "png"])
            
            # Save uploads to disk if provided
            attachments = []
            if schufa is not None:
                with open(os.path.join("temp", "schufa.pdf"), "wb") as f:
                    f.write(schufa.getbuffer())
                attachments.append(os.path.join("temp", "schufa.pdf"))
                
            if income is not None:
                with open(os.path.join("temp", "income.pdf"), "wb") as f:
                    f.write(income.getbuffer())
                attachments.append(os.path.join("temp", "income.pdf"))
                
            if id_doc is not None:
                ext = id_doc.name.split(".")[-1]
                with open(os.path.join("temp", f"id.{ext}"), "wb") as f:
                    f.write(id_doc.getbuffer())
                attachments.append(os.path.join("temp", f"id.{ext}"))
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Wohnungssuche", "Bewerbungen", "Debug"])
    
    with tab1:
        # Check if personal data is filled out
        required_fields = [st.session_state.first_name, st.session_state.last_name, 
                          st.session_state.email, st.session_state.phone]
        
        if not all(required_fields):
            st.warning("Bitte füllen Sie Ihre persönlichen Daten im Seitenmenü unter 'Persönliche Daten' aus, um Bewerbungen zu senden.")
        
        # Control buttons
        col1, col2 = st.columns([1, 3])
        with col1:
            search_button = st.button("🔍 Suche starten", use_container_width=True)
            demo_button = st.button("👥 Demo-Modus", use_container_width=True, help="Zeigt Beispiel-Wohnungen ohne echte Suche")
            
        # Selected sources
        sources = []
        if use_wg_gesucht:
            sources.append("wg_gesucht")
        if use_immoscout:
            sources.append("immoscout24")
        if use_immonet:
            sources.append("immonet")
        if use_immowelt:
            sources.append("immowelt")
        
        # Filter settings
        filters = {
            'location': location,
            'district': district,
            'min_price': min_price,
            'max_price': max_price,
            'min_size': min_size,
            'max_size': max_size,
            'min_rooms': min_rooms,
            'max_rooms': max_rooms,
            'balcony': balcony,
            'garden': garden,
            'elevator': elevator,
            'furnished': furnished,
            'pets_allowed': pets_allowed,
            'wg': allow_wg,
            'move_in_date': move_in_date,
            'floor': floor
        }
        
        # Application data
        application_data = {
            'first_name': st.session_state.first_name,
            'last_name': st.session_state.last_name,
            'email': st.session_state.email,
            'phone': st.session_state.phone,
            'gender': st.session_state.gender,
            'occupation': st.session_state.occupation,
            'message': st.session_state.custom_message
        }
        
        # Run search if button is clicked
        if search_button:
            if not sources:
                st.error("Bitte mindestens eine Quelle auswählen")
            else:
                with st.spinner("Suche läuft... Dies kann einige Minuten dauern."):
                    # Run the async search function
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(run_search(filters, sources))
                    
                    # Store results in session state
                    st.session_state.search_results = results
                    st.success(f"{len(results)} Wohnungen gefunden")
        
        # Demo mode - show example listings
        if demo_button:
            with st.spinner("Lade Demo-Wohnungen..."):
                # Create some example listings
                example_listings = [
                    {
                        'title': 'Schöne 2-Zimmer Wohnung in Berlin-Mitte',
                        'price': 950,
                        'size': 65,
                        'rooms': 2,
                        'location': 'Berlin',
                        'district': 'Mitte',
                        'url': 'https://example.com/listing1',
                        'source': 'immoscout24',
                        'image_url': 'https://via.placeholder.com/200x150?text=Apartment+1',
                        'has_balcony': True,
                        'has_garden': False,
                        'has_elevator': True,
                        'is_furnished': False,
                        'pets_allowed': True,
                        'is_wg': False,
                        'available_from': '2023-06-01',
                        'floor': '3. Stock'
                    },
                    {
                        'title': 'WG-Zimmer in Berlin-Kreuzberg',
                        'price': 550,
                        'size': 18,
                        'rooms': 1,
                        'location': 'Berlin',
                        'district': 'Kreuzberg',
                        'url': 'https://example.com/listing2',
                        'source': 'wg_gesucht',
                        'image_url': 'https://via.placeholder.com/200x150?text=WG+Room',
                        'has_balcony': False,
                        'has_garden': False,
                        'has_elevator': False,
                        'is_furnished': True,
                        'pets_allowed': False,
                        'is_wg': True,
                        'available_from': '2023-05-15',
                        'floor': '1. Stock'
                    },
                    {
                        'title': '3-Zimmer Wohnung mit Balkon und Garten',
                        'price': 1200,
                        'size': 80,
                        'rooms': 3,
                        'location': 'Berlin',
                        'district': 'Charlottenburg',
                        'url': 'https://example.com/listing3',
                        'source': 'immonet',
                        'image_url': 'https://via.placeholder.com/200x150?text=Apartment+3',
                        'has_balcony': True,
                        'has_garden': True,
                        'has_elevator': False,
                        'is_furnished': False,
                        'pets_allowed': True,
                        'is_wg': False,
                        'available_from': 'Sofort',
                        'floor': 'Erdgeschoss'
                    },
                    {
                        'title': 'Penthouse mit Dachterrasse in Berlin-Mitte',
                        'price': 1800,
                        'size': 100,
                        'rooms': 4,
                        'location': 'Berlin',
                        'district': 'Mitte',
                        'url': 'https://example.com/listing4',
                        'source': 'immowelt',
                        'image_url': 'https://via.placeholder.com/200x150?text=Penthouse',
                        'has_balcony': True,
                        'has_garden': False,
                        'has_elevator': True,
                        'is_furnished': True,
                        'pets_allowed': True,
                        'is_wg': False,
                        'available_from': '2023-06-15',
                        'floor': '6. Stock'
                    },
                    {
                        'title': 'Gemütliche 2-Zimmer Altbauwohnung in Prenzlauer Berg',
                        'price': 850,
                        'size': 55,
                        'rooms': 2,
                        'location': 'Berlin',
                        'district': 'Prenzlauer Berg',
                        'url': 'https://example.com/listing5',
                        'source': 'immoscout24',
                        'image_url': 'https://via.placeholder.com/200x150?text=Altbau',
                        'has_balcony': False,
                        'has_garden': False,
                        'has_elevator': False,
                        'is_furnished': False,
                        'pets_allowed': False,
                        'is_wg': False,
                        'available_from': '2023-07-01',
                        'floor': '2. Stock'
                    }
                ]
                
                # Apply basic filters to demo listings
                filtered_listings = []
                for listing in example_listings:
                    # Simple filtering for demo mode
                    if listing['price'] > filters['max_price']:
                        continue
                    if listing['rooms'] < filters['min_rooms'] or listing['rooms'] > filters['max_rooms']:
                        continue
                    if listing['size'] < filters['min_size']:
                        continue
                    if filters['district'] and filters['district'].lower() not in listing['district'].lower():
                        continue
                    if filters['balcony'] and not listing.get('has_balcony', False):
                        continue
                    if filters['garden'] and not listing.get('has_garden', False):
                        continue
                    if filters['elevator'] and not listing.get('has_elevator', False):
                        continue
                    if filters['furnished'] and not listing.get('is_furnished', False):
                        continue
                    if filters['pets_allowed'] and not listing.get('pets_allowed', False):
                        continue
                    if not filters['wg'] and listing.get('is_wg', False):
                        continue
                    
                    # Add to filtered listings
                    filtered_listings.append(listing)
                
                # Store results in session state
                st.session_state.search_results = filtered_listings
                st.success(f"{len(filtered_listings)} Demo-Wohnungen gefunden")
        
        # Display search results if available
        if 'search_results' in st.session_state:
            results = st.session_state.search_results
            
            # Create DataFrame for better display
            df_results = pd.DataFrame(results)
            
            if len(df_results) > 0:
                # Sort by price
                df_results = df_results.sort_values('price')
                
                # Display each listing as a card
                for index, row in df_results.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([1, 2, 1])
                        
                        with col1:
                            if row.get('image_url'):
                                st.image(row['image_url'], width=200)
                            else:
                                st.image("https://via.placeholder.com/200x150?text=No+Image", width=200)
                        
                        with col2:
                            st.subheader(row['title'])
                            
                            # Location display - account for possibly having district info
                            location_display = row['location']
                            if 'district' in row:
                                location_display = f"{row['district']}, {row['location']}"
                            elif '-' in row['location']:  # Handle old format like "Berlin-Mitte"
                                location_display = row['location']
                                
                            st.caption(f"📍 {location_display}")
                            
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Preis", f"{row['price']}€")
                            with col_b:
                                st.metric("Größe", f"{row['size']}m²")
                            with col_c:
                                st.metric("Zimmer", f"{row['rooms']}")
                            
                            # Show availability and floor if available
                            if 'available_from' in row or 'floor' in row:
                                avail = row.get('available_from', 'Nicht angegeben')
                                floor = row.get('floor', 'Nicht angegeben')
                                st.caption(f"Verfügbar ab: {avail} | Etage: {floor}")
                                
                            st.caption(f"Quelle: {row['source']}")
                            
                            # Add property feature indicators with emojis
                            features = []
                            if row.get('has_balcony'):
                                features.append("🏞️ Balkon")
                            if row.get('has_garden'):
                                features.append("🌳 Garten")
                            if row.get('has_elevator'):
                                features.append("🔼 Aufzug")
                            if row.get('is_furnished'):
                                features.append("🪑 Möbliert")
                            if row.get('pets_allowed'):
                                features.append("🐕 Haustiere")
                            if row.get('is_wg'):
                                features.append("👥 WG")
                            
                            if features:
                                st.markdown(" | ".join(features))
                        
                        with col3:
                            st.write(f"[Link zur Anzeige]({row['url']})")
                            
                            # Apply button
                            if 'id' in row:  # From database
                                if has_applied_to_listing(row['id']):
                                    st.info("Bereits beworben")
                                else:
                                    can_apply = all(required_fields)
                                    apply_btn = st.button(
                                        "Bewerben" if can_apply else "Daten fehlen", 
                                        key=f"apply_{index}", 
                                        use_container_width=True,
                                        disabled=not can_apply
                                    )
                                    
                                    if apply_btn:
                                        # Start application process
                                        with st.spinner("Bewerbung wird gesendet..."):
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)
                                            success, message = loop.run_until_complete(
                                                apply_to_listing(row.to_dict(), application_data, attachments)
                                            )
                                            
                                            if success:
                                                st.success(message)
                                            else:
                                                st.error(message)
                            else:  # New listing
                                can_apply = all(required_fields)
                                apply_btn = st.button(
                                    "Bewerben" if can_apply else "Daten fehlen", 
                                    key=f"apply_{index}", 
                                    use_container_width=True,
                                    disabled=not can_apply
                                )
                                
                                if apply_btn:
                                    # Start application process
                                    with st.spinner("Bewerbung wird gesendet..."):
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        success, message = loop.run_until_complete(
                                            apply_to_listing(row.to_dict(), application_data, attachments)
                                        )
                                        
                                        if success:
                                            st.success(message)
                                        else:
                                            st.error(message)
                        
                        st.divider()
            else:
                st.info("Keine Wohnungen gefunden. Bitte andere Filter verwenden.")
    
    with tab2:
        st.header("Bewerbungshistorie")
        
        if st.button("Aktualisieren"):
            st.session_state.applications = get_applied_listings()
        
        # Get application history from database
        if 'applications' not in st.session_state:
            st.session_state.applications = get_applied_listings()
            
        applications = st.session_state.applications
        
        if applications:
            # Create DataFrame for applications
            application_data = []
            for listing, application in applications:
                application_data.append({
                    'id': application.id,
                    'listing_title': listing.title,
                    'location': listing.location,
                    'price': listing.price,
                    'status': application.status,
                    'method': application.method,
                    'date': application.application_date,
                    'url': listing.url
                })
                
            df_applications = pd.DataFrame(application_data)
            df_applications = df_applications.sort_values('date', ascending=False)
            
            for index, row in df_applications.iterrows():
                with st.container():
                    cols = st.columns([3, 1, 1, 1, 1])
                    
                    with cols[0]:
                        st.write(f"**{row['listing_title']}**")
                        st.caption(f"📍 {row['location']}")
                        
                    with cols[1]:
                        st.write(f"{row['price']}€")
                        
                    with cols[2]:
                        status_color = {
                            'pending': 'blue',
                            'success': 'green',
                            'failed': 'red'
                        }.get(row['status'], 'gray')
                        
                        st.markdown(f"<span style='color:{status_color};'>●</span> {row['status'].capitalize()}", unsafe_allow_html=True)
                        
                    with cols[3]:
                        st.write(f"{row['method'].capitalize()}")
                        
                    with cols[4]:
                        st.write(f"{row['date'].strftime('%d.%m.%Y')}")
                        
                    st.divider()
        else:
            st.info("Noch keine Bewerbungen vorhanden.")

    # Debug tab content
    with tab3:
        st.header("Debug-Informationen")
        
        # Show current filters
        st.subheader("Aktuelle Filter")
        st.json(filters)
        
        # Show selected sources
        st.subheader("Ausgewählte Quellen")
        st.write(sources)
        
        # Show search results info
        if 'search_results' in st.session_state:
            st.subheader("Suchergebnisse")
            st.write(f"Anzahl der Ergebnisse: {len(st.session_state.search_results)}")
            
            # Show source breakdown
            if len(st.session_state.search_results) > 0:
                sources_count = {}
                for listing in st.session_state.search_results:
                    source = listing.get('source', 'unknown')
                    sources_count[source] = sources_count.get(source, 0) + 1
                
                st.write("Aufschlüsselung nach Quellen:")
                for source, count in sources_count.items():
                    st.write(f"- {source}: {count} Wohnungen")
                
                # Show first 3 listings in raw format for debugging
                st.subheader("Beispiel-Daten (Raw)")
                for i, listing in enumerate(st.session_state.search_results[:3]):
                    with st.expander(f"Wohnung {i+1}: {listing.get('title', 'No title')}"):
                        st.json(listing)
        
        # Add a manual scraper test button
        st.subheader("Scraper-Test")
        test_source = st.selectbox("Quelle zum Testen", 
                                  ["wg_gesucht", "immoscout24", "immonet", "immowelt"])
        
        if st.button("Scraper testen"):
            st.write(f"Test für {test_source} wird gestartet...")
            with st.spinner("Test läuft..."):
                try:
                    # Run a single scraper test
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Create a simple search filter
                    test_filters = {'location': 'Berlin', 'max_price': 2000}
                    
                    # Create and run the appropriate scraper
                    if test_source == "wg_gesucht":
                        scraper = WGGesuchtScraper()
                    elif test_source == "immoscout24":
                        scraper = ImmoScoutScraper()
                    elif test_source == "immonet":
                        scraper = ImmonetScraper()
                    elif test_source == "immowelt":
                        scraper = ImmoweltScraper()
                    
                    # Initialize, run search, and close
                    try:
                        await scraper.initialize()
                        test_results = await scraper.search(test_filters)
                        st.write(f"Test erfolgreich! {len(test_results)} Ergebnisse gefunden.")
                        
                        # Show sample results
                        if test_results:
                            with st.expander("Beispiel-Ergebnisse"):
                                st.json(test_results[:3])
                    finally:
                        await scraper.close()
                        
                except Exception as e:
                    st.error(f"Fehler beim Testen des Scrapers: {e}")
        
        # Add system info
        st.subheader("System-Informationen")
        st.write(f"Python-Version: {sys.version}")
        st.write(f"Platform: {sys.platform}")
        st.write(f"Working Directory: {os.getcwd()}")

# Run the main app
if __name__ == "__main__":
    main() 