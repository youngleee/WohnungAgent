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
    search_manager = SearchManager(sources=search_sources)
    try:
        await search_manager.initialize_scrapers(headless=True)
        listings = await search_manager.search_all(filters)
        all_listings = search_manager.combine_with_database(listings, filters)
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
def save_to_session_state(key, value):
    st.session_state[key] = value
    # Save to browser local storage using Streamlit components
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
                                     on_change=save_to_session_state, args=("first_name",), key="input_first_name")
                                     
            last_name = st.text_input("Nachname", value=st.session_state.last_name,
                                    on_change=save_to_session_state, args=("last_name",), key="input_last_name")
                                    
            email = st.text_input("E-Mail", value=st.session_state.email,
                                on_change=save_to_session_state, args=("email",), key="input_email")
                                
            phone = st.text_input("Telefon", value=st.session_state.phone,
                                on_change=save_to_session_state, args=("phone",), key="input_phone")
                                
            gender = st.selectbox("Anrede", options=["male", "female"], 
                                format_func=lambda x: "Herr" if x == "male" else "Frau",
                                index=0 if st.session_state.gender == "male" else 1,
                                on_change=save_to_session_state, args=("gender",), key="input_gender")
                                
            occupation = st.text_input("Beruf", value=st.session_state.occupation,
                                     on_change=save_to_session_state, args=("occupation",), key="input_occupation")
            
            custom_message = st.text_area("Persönliche Nachricht", 
                                        value=st.session_state.custom_message,
                                        height=100,
                                        help="Diese Nachricht wird in Bewerbungen eingefügt.",
                                        on_change=save_to_session_state, args=("custom_message",), key="input_custom_message")
            
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
    tab1, tab2 = st.tabs(["Wohnungssuche", "Bewerbungen"])
    
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

# Run the main app
if __name__ == "__main__":
    main() 