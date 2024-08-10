from io import StringIO
from datetime import datetime
import google.generativeai as genai
import os
import time  # Import the time module
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Canvas,Label 
from PIL import Image, ImageTk
import pandas as pd
import json
from pathlib import Path
import db
import mysql.connector
import numpy as np
global cnx

class  DataSnapAI:
    def __init__(self, api_key, root):
        self.API_KEY = api_key
        genai.configure(api_key=self.API_KEY)
        self.estimated_price=0   
        # Model Configuration
        self.MODEL_CONFIG = {
            "temperature": 0.1,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 4096,
        }

        # Safety Settings of Model
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]

        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config=self.MODEL_CONFIG,
            safety_settings=self.safety_settings
        )

        self.directory_path = ""
        self.image_files = []
        
        self.Currency="₹"
        # UI Elements
               
        self.root = root
        self.root.title("DataSnap AI - The AI Powered Data Entry Module")
        self.root.geometry("1024x768")
        self.set_background("#f2ae2f") 
        # self.root.resizable(False, False)  # Disable window resizing
      
        # Create a Canvas widget to display the background image
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Image file name
        image_file = 'BGImages\\bg.png'  # Replace with your image file name

        # Construct the full path to the image
        image_path = os.path.join(current_dir, image_file)
        bg_image = Image.open(image_path)
        bg_image = bg_image.resize((1024, 768), Image.LANCZOS)             
        self.bg_photo = ImageTk.PhotoImage(bg_image)

        # Create a Canvas widget to display the background image
        self.canvas = Canvas(root, width=1024, height=768,background="#f2ae2f")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # # Create a Label widget to display the background image
       
        self.select_button = tk.Button(root, text="Select Directory", command=self.select_directory, bg="#007BFF", fg="white", font=("Arial", 14, "bold"))
        self.select_button.place(relx=0.1, rely=0.8, anchor="center")
                
        self.process_button = tk.Button(root, text="Process Images", command=self.process_images, state=tk.DISABLED, bg="#28A745", fg="white", font=("Arial", 14, "bold"))
        self.process_button.place(relx=0.3, rely=0.8, anchor="center")
         # Loading indicator
        self.progress = ttk.Progressbar(root, mode='indeterminate')

        self.image_path_label = tk.Label(root, text="", font=("Arial", 12), background="#f2ae2f")
        self.image_path_label.pack(pady=10)
    
        self.processing_time_label = ttk.Label(root, text="", font=("Arial", 12), background="#f2ae2f")
        self.processing_time_label.pack(pady=10)
        
        self.send_button = tk.Button(root, text="Send Data",state=tk.DISABLED,command=self.send_data,bg="#28A745", fg="white", font=("Arial", 14, "bold"))
       
        # self.send_button.place(relx=0.3, rely=0.8, anchor="w")
        # self.send_button = tk.Button(self.root, text="Send Data", command=self.send_data, bg="#FFC107", fg="black", font=("Arial", 14, "bold"))
        # self.send_button.place(relx=0.5, rely=0.45, anchor="center")
        self.send_button.pack(pady=10)
        self.send_button.pack_forget()
     
        self.tree = None        
        self.items_tree = None
       
    def clear_tree(self):
        if self.tree:                
            for item in self.tree.get_children():
                self.tree.delete(item)

    def send_data(self):
        self.clear_tree()                          
        messagebox.showinfo("Processing Complete", "Data sent successfully! \nThank you for using DataSnap AI.")
          
    def select_directory(self):
        self.directory_path = filedialog.askdirectory()
        if self.directory_path:
            self.image_files = self.get_image_files(self.directory_path)
            if self.image_files:
                self.process_button.config(state=tk.NORMAL)
            else:
                messagebox.showinfo("No Images", "No images found in the selected directory.")
                self.process_button.config(state=tk.DISABLED)
    def get_image_files(self, directory_path):
        image_patterns = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"]
        image_files = []
        for pattern in image_patterns:
            image_files.extend(glob.glob(os.path.join(directory_path, pattern)))
        return image_files
    def show_loading(self):
        self.loading_label = ttk.Label(self.root, text="Processing Images...", font=("Arial", 16), background="white")
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

    def hide_loading(self):
        self.loading_label.destroy()
    def set_background(self, color):
        self.root.configure(bg=color)
        for widget in self.root.winfo_children():
            if isinstance(widget, (tk.Frame, tk.Label, tk.Button, ttk.Label)):
                widget.configure(bg=color)
    
    def fetch_data_from_db(self, inv_id):
        try:
            # Connect to the database
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root",
                database="testdb"
            )
            cursor = conn.cursor(dictionary=True)
            
            # Fetch data from tbl_invoice
            cursor.execute("SELECT * FROM tbl_invoice WHERE Inv_Id = %s", (inv_id,))
            invoice_data = cursor.fetchone()

            # Fetch data from tbl_item
            cursor.execute("SELECT * FROM tbl_item WHERE INVOICE_ID = %s", (inv_id,))
            item_data = cursor.fetchall()

            cursor.close()
            conn.close()

            return invoice_data, item_data

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
            return None, None

    def process_images(self):
        if self.image_files:
            self.root.state('zoomed')
            # Start the loading indicator
            self.progress.pack(pady=10)
            self.progress.start()

            # Start the timer
            start_time = time.time()

            # Simulating image processing
            # self.show_loading()
            # time.sleep(3)  # Simulating processing time
            # self.hide_loading()

            # Clear previous results
            if self.tree:
                self.tree.destroy()
        
            # Clear the canvas
            # self.canvas.delete("bg_Image")
            self.canvas.destroy()
            # Create treeview to display invoice and item details
            columns = [
                "COMPANY_NAME", "FROM", "BILL_TO", "SHIP_TO", "INVOICE_NO", 
                "INVOICE_DATE", "PO", "SUBTOTAL", "DUE_DATE", "GST", 
                "TOTAL", "TERMS_AND_CONDITION", "BANK_NAME", "ACCOUNT_NUMBER", "ROUTING_NUMBER"
            ]
            self.tree = ttk.Treeview(self.root, columns=columns, show="tree headings")
            # self.tree = ttk.Treeview(self.root, columns=columns, show="headings", style="Treeview")
            self.tree.heading("#0", text="Invoice/Item")
            for col in columns:
                self.tree.heading(col, text=col,anchor='w')
                self.tree.column(col, width=100,anchor="w")
                                
            self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

            for image_path in self.image_files:
                # Placeholder for actual image processing to get inv_id
                # inv_id = 4  # Replace with the actual way to obtain Inv_Id
                inv_id = extractor.chtwithImages(image_path)
                invoice_data, item_data = self.fetch_data_from_db(inv_id)

                if invoice_data:
                    invoice_id = self.tree.insert("", tk.END, text="Invoice", values=[
                        invoice_data["COMPANY_NAME"], invoice_data["FROM"], invoice_data["BILL_TO"], invoice_data["SHIP_TO"],
                        invoice_data["INVOICE_NO"], invoice_data["INVOICE_DATE"], invoice_data["PO"], invoice_data["SUBTOTAL"],
                        invoice_data["DUE_DATE"], invoice_data["GST"], invoice_data["TOTAL"], invoice_data["TERMS_AND_CONDITION"],
                        invoice_data["BANK_NAME"], invoice_data["ACCOUNT_NUMBER"], invoice_data["ROUTING_NUMBER"], "", "", "", ""
                    ])
                    
                    # self.tree.place(relx=0.1, rely=0.2, relwidth=0.8, relheight=0.2)
                    if item_data:
                        self.tree.insert(invoice_id, tk.END, text=" ", values=[
                                "DESCRIPTION", "QTY", "UNITPRICE","AMOUNT"
                            ])
                        for item in item_data:
                            self.tree.insert(invoice_id, tk.END, text="Item", values=[
                                item["DESCRIPTION"], item["QTY"], item["UNITPRICE"], item["AMOUNT"]                                
                            ])
                        # self.item_tree.place(relx=0.1, rely=0.5, relwidth=0.8, relheight=0.2)
                    # self.send_button = tk.Button(self.root, text="Send Data", command=self.send_data, bg="#FFC107", fg="black", font=("Arial", 14, "bold"))
                    # self.send_button.place(relx=0.5, rely=0.45, anchor="center")
                    self.send_button.config(state=tk.NORMAL)
                    self.send_button.pack(pady=10)
                 
                    
                self.image_path_label.config(text=image_path)
                self.root.update_idletasks()  # Update the GUI to show the current image path
           
            # Stop the loading indicator
            self.progress.stop()
            self.progress.pack_forget()

            # Stop the timer
            end_time = time.time()
            processing_time = end_time - start_time
            processing_time_minutes = processing_time / 60
            self.processing_time_label.config(text=f"Processing Time: {processing_time_minutes:.2f} minutes") 
            # self.processing_time_label.config(text=f"Processing Time: {processing_time:.2f} seconds, Cost:{self.estimated_price}")            
            # self.root.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height() + self.tree.winfo_height()}")
            # Maximize the window
            self.root.state('zoomed')
            messagebox.showinfo("Processing Complete", "All images have been processed.")
        else:
            self.image_path_label.config(text="No images found.")
      
    def convert_currency_to_float(self,currency_value):
        try:
            currency_value = str(currency_value)
            if(currency_value is not None and currency_value != 'nan'):
                # Remove the currency symbol and any commas
                amount_str = currency_value.replace('₹', '').replace(',', '')
                
                # Convert to float
                amount_float = float(amount_str)
                
                # Convert to numpy int64
                # amount_float64 = np.float64(amount_float)
                if amount_float is not None:
                    return amount_float
                else :
                    return 0
            else :
                return 0    
        except ValueError as e:
            print(f"Error converting currency: {e}")
            return None    
    def convert_currency_to_int(self,currency_value):
        try:
            currency_value = str(currency_value)
            if(currency_value is not None and currency_value != 'nan'):
                # Remove the currency symbol and any commas
                amount_str = currency_value.replace('₹', '').replace(',', '')
                
                # Convert to float
                amount_float = float(amount_str)
                
                # Convert to int
                amount_int = int(amount_float)
                if amount_int is not None:
                    return amount_int
                else :
                    return 0
            else:
                return 0
        except ValueError as e:
            print(f"Error converting currency: {e}")
            return None
    def convert_date_format(self, date_str):
        try:
            date_str=str(date_str)
            if(date_str is not None and date_str != 'nan'):
                # Convert the date from DD/MM/YYYY to YYYY-MM-DD
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                return date_obj.strftime('%Y-%m-%d')
            else:
                return None
        except ValueError as e:
            print(f"Error converting date: {e}")
            return None
    def gemini_output(self, image_path, system_prompt, user_prompt):
        img = Path(image_path)
        if not img.exists():
            raise FileNotFoundError(f"Could not find image: {img}")
        
        image_parts = [
            {
                "mime_type": "image/png",  # Mime types: PNG - image/png, JPEG - image/jpeg, WEBP - image/webp
                "data": img.read_bytes()
            }
        ]
        
        input_prompt = [system_prompt, image_parts[0], user_prompt]
        response = self.model.generate_content(input_prompt)
        return response
    def convert_to_list_of_dicts(self,data):
        """Converts mixed data structure to a list of dictionaries."""
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return [self.convert_to_list_of_dicts(item) for item in data]
        else:
            return []
    def create_Invoice(self,COMPANY_NAME, FROM, BILL_TO, SHIP_TO, INVOICE_NO, INVOICE_DATE, PO, SUBTOTAL, DUE_DATE, GST, TOTAL, TERMS_AND_CONDITION, BANK_NAME, ACCOUNT_NUMBER, ROUTING_NUMBER, items):
        # response=""
        inv_id=0
         # connect to mysql
        cnx = mysql.connector.connect(host="localhost",
        user="root",
        password="root",
        database="testdb")
        cursor = cnx.cursor()
        try:        
           
            args = (
                str(INVOICE_NO) if pd.notna(INVOICE_NO) else "N/A",
                str(INVOICE_DATE) if pd.notna(INVOICE_DATE) else " ",
                str(COMPANY_NAME) if pd.notna(COMPANY_NAME) else "N/A",
                str(FROM) if pd.notna(FROM) else "N/A",
                str(BILL_TO) if pd.notna(BILL_TO) else "N/A",
                str(SHIP_TO) if pd.notna(SHIP_TO) else "N/A",
                str(PO) if pd.notna(PO) else "0",
                float(SUBTOTAL) if pd.notna(SUBTOTAL) else 0.0,
                str(DUE_DATE) if pd.notna(DUE_DATE) else " ",
                float(GST) if pd.notna(GST) else 0.0,
                float(TOTAL) if pd.notna(TOTAL) else 0.0,
                str(TERMS_AND_CONDITION) if pd.notna(TERMS_AND_CONDITION) else "N/A",
                str(BANK_NAME) if pd.notna(BANK_NAME) else "N/A",
                str(ACCOUNT_NUMBER) if pd.notna(ACCOUNT_NUMBER) else "N/A",
                str(ROUTING_NUMBER) if pd.notna(ROUTING_NUMBER) else "N/A",
                int(0)  # Output parameter for Inv_Id
            )
            print(args)
            # Execute the stored procedure
            cursor.callproc('sp_InsertInvoice', args)

            # Fetch the Inv_Id
            inv_id = 0
            for result in cursor.stored_results():
                row = result.fetchone()
                if row:
                    inv_id = row[0]
            print(f"Inserted invoice with Inv_Id: {inv_id}")

            # Insert items related to the invoice
            for index, item in items.iterrows():
                qty_str =str(item.get('QTY',0))
                unitprice_str =str(item.get('UNITPRICE',0.0))
                QTY = self.convert_currency_to_int(qty_str)
                UNITPRICE = self.convert_currency_to_float(unitprice_str)
                
                if QTY is not None and UNITPRICE is not None:
                    item_args = (
                       item.get('DESCRIPTION', f"item-{index+1}"),  # Use 'item-n' for missing descriptions
                       QTY, UNITPRICE, int(inv_id)
                    )
                    print(item_args)
                    try:
                        cursor.callproc('sp_InsertItem', item_args)
                    except mysql.connector.Error as err:
                        print(f"Error inserting invoice item: {err}")
                else:
                    print(f"Invalid data for item: {item}")
            # Commit the transaction
            cnx.commit()

            # Closing the cursor
            cursor.close()
            cnx.close()
            # response = "Invoice created successfully!"
            return inv_id

        except mysql.connector.Error as err:
            response=f"Error inserting invoice item: {err}"
            print(err)
            # Rollback changes if necessary
            cnx.rollback()                  
        except Exception as e:
            response=f"An error occurred: {e}"
            print(e)
            # Rollback changes if necessary
            cnx.rollback()       
        finally:
            # Close the connection
            cursor.close()
            cnx.close()
            return inv_id
    def calculate_gemini_price(result, input_tokens=None, output_tokens=None):
        """Estimates the price of processing a request using Gemini 1.5 Pro.

        Args:
            result: The output returned by the `gemini_output` function (likely contains text).
            input_tokens (int, optional): The number of tokens in the system and user prompts (if known). Defaults to None.
            output_tokens (int, optional): The number of tokens in the generated response (if known). Defaults to None.

        Returns:
            float: The estimated price of the request in USD.

        Raises:
            ValueError: If both input_tokens and output_tokens are None.
        """

        # Error handling for missing token counts
        if input_tokens is None and output_tokens is None:
            raise ValueError("Either input_tokens or output_tokens must be provided.")

        # Estimate output tokens if not provided
        if output_tokens is None:
            # Replace this with your logic to estimate output tokens from the result
            output_tokens = len(result.text.split()) * 2  # Placeholder assuming 2 tokens per word

        # Total tokens (account for both input and output)
        total_tokens = input_tokens + output_tokens

        # Price per million tokens based on usage tier
        price_per_million = 1.75 if total_tokens <= 128000 else 3.50

        # Calculate estimated cost
        estimated_cost = price_per_million * total_tokens / 1000000

        rounded_price = round(estimated_cost, 2)

        return rounded_price
         
    def estimate_input_tokens(self,system_prompt, user_prompt):
        """Estimates the number of tokens in system and user prompts.
        Args:
            system_prompt (str): The system prompt provided to Gemini.
            user_prompt (str): The user prompt provided to Gemini.

        Returns:
            int: The estimated number of tokens in both prompts.
        """

        # Replace this with your logic for tokenization (e.g., using a tokenizer library)
        # Here's a simple word-based estimation (might be inaccurate)
        total_words = len(system_prompt.split()) + len(user_prompt.split())
        # Assuming an average of 2 tokens per word (adjust based on your language)
        estimated_tokens = total_words * 2
        return estimated_tokens

    def chtwithImages(self,imagepath):
        ########## Chat with image ############
        system_prompt = """
            You are a specialist in comprehending receipts.
            Input images in the form of receipts will be provided to you,
            and your task is to respond to questions based on the content of the input image.
        """
        
        # image_path = "./Images/Inv_Handwritten.png"
        image_path = imagepath
        # image_path = "./Images/inv04.jpg"
        # user_prompt = """
        #     Convert Invoice data into json format with appropriate json tags as required for the data in image.
        #     I am going to provide a template for your output. CAPITALIZED WORDS are my placeholders for json tags.
        #     Try to fit the output into one or more of the placeholders that I list.
        #     Please preserve the formatting and overall template that I provide. 
        #     This is the template: COMPANY_NAME, FROM, BILL_TO, SHIP_TO, INVOICE_NO, INVOICE_DATE, 
        #     P.O, DUE_DATE, SUBTOTAL, GST, TOTAL, TERMS_AND_CONDITION, BANK_NAME, ACCOUNT_NUMBER, ROUTING_NUMBER,CURRENCY,
        #     ITEMS[QTY, DESCRIPTION, UNITPRICE, AMOUNT].Replace all null values with 0 or blank space base on the column data type.
        # """

        user_prompt =""" 
        Convert Invoice data into JSON format suitable for MySQL database insertion.forget about previous data,freshly process each image that I provide you.I am going to provide a template for your output.Try to fit the output into one or more of the placeholders that I list.
                {
                "COMPANY_NAME": ?,
                "FROM": ?,
                "BILL_TO": ?,
                "SHIP_TO": ?,
                "INVOICE_NO": ?,
                "INVOICE_DATE": ?,  //Asume Date as Invoice date, feed the data in 'YYYY-MM-DD' format,Replace with ' ' format if missing
                "P.O": ?,
                "DUE_DATE": ?,  // Replace with 'YYYY-MM-DD' format or ' ' if missing
                "SUBTOTAL": ?,  // Replace with 0.0 if missing
                "GST": ?,  // Replace with 0.0 if missing
                "TOTAL": ?,  // Replace with 0.0 if missing
                "TERMS_AND_CONDITION": ?,
                "BANK_NAME": ?,
                "ACCOUNT_NUMBER": ?,
                "ROUTING_NUMBER": ?,
                "CURRENCY": ?,  // Replace with 'USD' or relevant currency code if missing
                "ITEMS": [
                    {
                    "QTY": ?,
                    "DESCRIPTION": ?,
                    "UNITPRICE": ?,  // Replace with 0.0 if missing
                    "AMOUNT": ?  // Replace with 0.0 if missing
                    }
                ]
                }
            """
        # print(user_prompt)
        #commented to test locally
        result = self.gemini_output(image_path, system_prompt, user_prompt)
      
        input_tokens = self.estimate_input_tokens(system_prompt,user_prompt)  # Replace with actual number of tokens from your prompts

        # Option 1: If you can estimate output tokens from the result
        output_tokens = len(result.text.split()) * 2

        # Option 2: If you cannot estimate output tokens, omit the argument
        price_for_request = self.calculate_gemini_price(input_tokens,output_tokens)
        self.estimated_price = self.estimated_price + price_for_request
        
        print(f"Estimated price for processing this request: ${self.estimated_price:.2f}")
                
        # Remove leading and trailing ```json and ``` characters

        ### commentto test locally#########
        json_string_cleaned = result.text.strip('```json\n').strip('```')

        ## JUST TO TEST LOCALY
        # json_string_cleaned = '{"COMPANY_NAME": "Saffron Design", "FROM": "77 Namrata Bldg\\nDelhi, Delhi 400077", "BILL_TO": "Kavindra Mannan\\n27, Dlf City, Gupta\\nDelhi, Delhi 40003", "SHIP_TO": "Kavindra Mannan\\n264, Abdul Rehman\\nMumbai, Bihar 40009", "INVOICE_NO": "IN-001", "INVOICE_DATE": "29/01/2019", "P.O": "2430/2019", "DUE_DATE": "26/04/2019", "SUBTOTAL": "12,246.00", "GST": "1,469.52", "TOTAL": "13,715.52", "TERMS_AND_CONDITION": "Payment is due within 15 days", "BANK_NAME": "State Bank of India", "ACCOUNT_NUMBER": "12345678", "ROUTING_NUMBER": "09876543210", "CURRENCY": "₹", "ITEMS": [{"QTY": "1", "DESCRIPTION": "Frontend design restructure", "UNITPRICE": "9,999.00", "AMOUNT": "9,999.00"}, {"QTY": "2", "DESCRIPTION": "Custom icon package", "UNITPRICE": "975.00", "AMOUNT": "1,950.00"}, {"QTY": "3", "DESCRIPTION": "Gandhi mouse pad", "UNITPRICE": "99.00", "AMOUNT": "297.00"}]}'
        json_io = StringIO(json_string_cleaned)
        ############################
        # Read the JSON string into a pandas DataFrame using StringIO
        try:
            ### commentto test locally#########
            json_df = pd.read_json(json_io)            
            ##################################
            # for testing
            # json_df=invoice_data
        except ValueError as e:
            print(f"Error reading JSON: {e}")
            return

        # Accessing columns
        try:
            # print(json_df)
            COMPANY_NAME = json_df["COMPANY_NAME"].iloc[0] if not pd.isna(json_df["COMPANY_NAME"].iloc[0]) else "N/A"
            FROM = json_df["FROM"].iloc[0] if not pd.isna(json_df["FROM"].iloc[0]) else "N/A"
            BILL_TO = json_df["BILL_TO"].iloc[0] if not pd.isna(json_df["BILL_TO"].iloc[0]) else "N/A"
            SHIP_TO = json_df["SHIP_TO"].iloc[0] if not pd.isna(json_df["SHIP_TO"].iloc[0]) else "N/A"
            INVOICE_NO = json_df["INVOICE_NO"].iloc[0] if not pd.isna(json_df["INVOICE_NO"].iloc[0]) else "N/A"
            INVOICE_DATE = json_df["INVOICE_DATE"].iloc[0] if not pd.isna(json_df["INVOICE_DATE"].iloc[0]) else " "
                       
            # if INVOICE_DATE != None : 
            #     INVOICE_DATE=self.convert_date_format(INVOICE_DATE) 
            # else :
            #     INVOICE_DATE="1999-01-01"

            PO = json_df["P.O"].iloc[0] if not pd.isna(json_df["P.O"].iloc[0]) else "0"

            subtotal_str =str(json_df["SUBTOTAL"].iloc[0]) if not pd.isna(json_df["SUBTOTAL"].iloc[0]) else "0"
            SUBTOTAL = self.convert_currency_to_float(subtotal_str)
                                 
            gst_str = str(json_df["GST"].iloc[0]) if not pd.isna(json_df["GST"].iloc[0]) else "0"
            GST = self.convert_currency_to_float(gst_str)

            total_str = str(json_df["TOTAL"].iloc[0]) if not pd.isna(json_df["TOTAL"].iloc[0]) else "0"
            TOTAL = self.convert_currency_to_float(total_str)

            # SUBTOTAL = json_df["SUBTOTAL"][0]          
            # GST = json_df["GST"][0]
            # TOTAL = json_df["TOTAL"][0]
            
            DUE_DATE = json_df["DUE_DATE"].iloc[0] if not pd.isna(json_df["DUE_DATE"].iloc[0]) else " "
            # if DUE_DATE != None :
            #     DUE_DATE=self.convert_date_format(DUE_DATE) 
            # else :
            #     DUE_DATE="1999-01-01"
            TERMS_AND_CONDITION = json_df["TERMS_AND_CONDITION"].iloc[0] if not json_df["TERMS_AND_CONDITION"].iloc[0] else "N/A"
            BANK_NAME = json_df["BANK_NAME"].iloc[0] if not pd.isna(json_df["BANK_NAME"].iloc[0]) else  "N/A"
            ACCOUNT_NUMBER = json_df["ACCOUNT_NUMBER"].iloc[0] if not pd.isna(json_df["ACCOUNT_NUMBER"].iloc[0]) else "0"
            ROUTING_NUMBER = json_df["ROUTING_NUMBER"].iloc[0] if not pd.isna(json_df["ROUTING_NUMBER"].iloc[0]) else "0"
            CURRENCY = json_df["CURRENCY"].iloc[0] if not pd.isna(json_df["CURRENCY"].iloc[0]) else "₹"

            items = pd.json_normalize(json_df["ITEMS"])
            self.Currency = CURRENCY
            # to test locally
            # items=items_data
            print("COMPANY_NAME:")
            print(COMPANY_NAME)
            print("\nFROM:")
            print(FROM)
            print("\nBILL_TO:")
            print(BILL_TO)
            print("\nSHIP_TO:")
            print(SHIP_TO)
            print("\nINVOICE_NO:")
            print(INVOICE_NO)
            print("\nINVOICE_DATE:")
            print(INVOICE_DATE)
            print("\nPO:")
            print(PO)
            print("\nSUBTOTAL:")
            print(SUBTOTAL)
            print("\nDUE_DATE:")
            print(DUE_DATE)
            print("\nGST:")
            print(GST)
            print("\nTOTAL:")
            print(TOTAL)
            print("\nTERMS_AND_CONDITION:")
            print(TERMS_AND_CONDITION)
            print("\nBANK_NAME:")
            print(BANK_NAME)
            print("\nACCOUNT_NUMBER:")
            print(ACCOUNT_NUMBER)
            print("\nROUTING_NUMBER:")
            print(ROUTING_NUMBER)
            print(CURRENCY)
            res = self.create_Invoice(COMPANY_NAME,FROM,BILL_TO,SHIP_TO,INVOICE_NO,INVOICE_DATE,PO,SUBTOTAL,DUE_DATE,GST,TOTAL,TERMS_AND_CONDITION,BANK_NAME,ACCOUNT_NUMBER,ROUTING_NUMBER,items)
            #res = db.create_invoice()
            # print(res)            
            # print("\nItems:")
            # print(items)
            return res
        except KeyError as e:
            print(f"Error: Missing key in JSON data: {e}")
            return 0
    
# Example usage
if __name__ == "__main__":      
   api_key = 'your API key'  # Use your actual API key
   root = tk.Tk()
   extractor = DataSnapAI(api_key,root)
   root.mainloop()

#    img_path="./Images/Inv_Handwritten.png"   
#    extractor.Extraction(img_path)
