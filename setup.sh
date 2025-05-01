#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright
playwright install chromium

# Create necessary directories
mkdir -p temp templates database

# Copy templates if they don't exist
if [ ! -f "templates/email_template.html" ]; then
    echo "Setting up default email template"
    cp templates/email_template.html.default templates/email_template.html
fi

if [ ! -f "templates/form_template.txt" ]; then
    echo "Setting up default form template"
    cp templates/form_template.txt.default templates/form_template.txt
fi

echo "Setup complete!" 