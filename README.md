# DataSnapAI
DataSnapAI is a tool for extracting and analysing data from images like invoices and receipts. Using the Google Gemini API,it converts unstructured data into structured JSON formats, automating data entry and reducing errors.Key features : Image Data Extraction, Structured Output and Versatile Input Support.Built with Python,Google Gemini API and Pandas.

# Features

Extracts data from images of invoices and receipts.

Converts unstructured image data into structured JSON format.

Integrates with Google Gemini API for advanced data processing.

Configurable MySQL database for data storage and management.

# Installation

## Prerequisites

Python 3.9 installed on your machine.

MySQL database installed and running.

Google Gemini API Key.

Git installed for version control.

## Installation Guide

Step 1: Clone the Repository

git clone https://github.com/namita0710/DataSnapAI.git

cd DataSnapAI

Step 2: Set Up the Virtual Environment

 command: python -m venv venv
 
 On Windows use `venv\Scripts\activate`

Step 3: Install Required Dependencies

  command: pip install -r requirements.txt

## Database Setup

Step 1: Create the MySQL Database

Open MySQL (via command line or a GUI tool like MySQL Workbench).

Create the Database:

  CREATE DATABASE testdb;

Import the Schema:

  Import the DataSnapAi.sql file to create the necessary tables:

## Google Gemini API Configuration

  Obtain Your API Key:
  
  Sign up for the Google Gemini API and obtain your API key.

## Configure the API Key:

  Open the datasnapai.py file and replace the placeholder with your actual API key:
  
  api_key = 'your_actual_api_key_here'
  
## Running and testing the Application

Step 1: Verify the Setup

    Ensure all dependencies are installed and the MySQL database is configured as described in the previous sections.

Step 2: Pre Process Images

    Place all your invoice Images into one directory

Step 3: Run the Python Script

    python datasnapai.py

Step 4: Process Images

    Open Datasnap AI and select that directory.
    
    Now, Click on Process Images,it will process all those images and convert them into some meaningfull data.   

Step 5: Send Data

    The processed data will be displayed on the screen.
    
    Now, click on send data button to send all processed data into your existing system
    
    (your data entry code to your existing system will goes here)
    
## Contributing

We welcome contributions from the community. Please feel free to fork the repository, make changes, and submit a pull request.

