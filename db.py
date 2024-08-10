import asyncio
import aiomysql
import pandas as pd

# Database configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'db': 'testdb',
    'charset': 'utf8mb4',
    'autocommit': True,
}

# Invoice data
invoice_data = {
            'INVOICE_NO': 'INV12345',
            'INVOICE_DATE': '2024-05-24',
            'COMPANY_NAME': 'Your Company',
            'Tbl_Invoicecol': 'value',
            'FROM': 'Your Address',
            'BILL_TO': 'Client Address',
            'SHIP_TO': 'Client Shipping Address',
            'PO': 'PO12345',
            'SUBTOTAL': 100.00,
            'DUE_DATE': '2024-06-24',
            'GST': 5.00,
            'TOTAL': 105.00,
            'TERMS_AND_CONDITION': 'Payment within 30 days',
            'BANK_NAME': 'Your Bank',
            'ACCOUNT_NUMBER': '1234567890',
            'ROUTING_NUMBER': '0987654321'
        }

# Items data
items_data = [
    {'QTY': 1, 'DESCRIPTION': 'Frontend design restructure', 'UNITPRICE': 9999.00, 'AMOUNT': 9999.00},
    {'QTY': 2, 'DESCRIPTION': 'Custom icon package', 'UNITPRICE': 975.00, 'AMOUNT': 1950.00},
    {'QTY': 3, 'DESCRIPTION': 'Gandhi mouse pad', 'UNITPRICE': 99.00, 'AMOUNT': 297.00},
]

async def create_invoice(COMPANY_NAME, FROM, BILL_TO, SHIP_TO, INVOICE_NO, INVOICE_DATE, PO, SUBTOTAL, DUE_DATE, GST, TOTAL, TERMS_AND_CONDITION, BANK_NAME, ACCOUNT_NUMBER, ROUTING_NUMBER, items):
    try:
        # Connect to the database        
        async with aiomysql.create_pool(**DATABASE_CONFIG) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Call the stored procedure to insert invoice
                     # Call the stored procedure
                    args = (
                        INVOICE_NO, INVOICE_DATE, COMPANY_NAME, FROM,BILL_TO,SHIP_TO,PO,SUBTOTAL,DUE_DATE,GST,TOTAL,TERMS_AND_CONDITION,BANK_NAME,ACCOUNT_NUMBER,ROUTING_NUMBER,
                        0  # This will be the output parameter for Inv_Id
                    )

                    # await cursor.execute(
                    #     "CALL sp_InsertInvoice(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, @p_Inv_Id)",
                    #     (
                    #         invoice_data['INVOICE_NO'], invoice_data['INVOICE_DATE'], invoice_data['COMPANY_NAME'],
                    #         invoice_data['FROM'], invoice_data['BILL_TO'], invoice_data['SHIP_TO'], invoice_data['PO'],
                    #         invoice_data['SUBTOTAL'], invoice_data['DUE_DATE'], invoice_data['GST'], invoice_data['TOTAL'],
                    #         'Payment within 30 days', 'Your Bank', '1234567890', '0987654321',0
                    #     )
                    # )
                    await cursor.callproc('sp_InsertInvoice', args)
                    # Fetch the invoice ID
                    await cursor.execute("SELECT @p_Inv_Id")
                    result = await cursor.fetchone()
                    inv_id = result[0]

                    print(f"Inserted invoice with Inv_Id: {inv_id}")

                    # Insert items related to the invoice
                    for item in items_data:
                        await cursor.execute(
                            "CALL sp_InsertItem(%s, %s, %s, %s)",
                            (item['DESCRIPTION'], item['QTY'], item['UNITPRICE'], inv_id)
                        )

                    print("Items inserted successfully.")

    except aiomysql.Error as e:
        print(f"Error: {e}")
    finally:
            pool.close()
            await pool.wait_closed()
        
# loop = asyncio.get_event_loop()
# loop.run_until_complete(create_invoice())
