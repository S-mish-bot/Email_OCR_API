import string
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
#from utility_script import *

# Function to find the bounding region
def format_bounding_region(bounding_regions):
    if not bounding_regions:
        return "N/A"
    return ", ".join("Page #{}: {}".format(region.page_number, format_bounding_box(region.bounding_box)) for region in bounding_regions)


# Function to find the bounding Box
def format_bounding_box(bounding_box):
    if not bounding_box:
        return "N/A"
    return ", ".join(["[{}, {}]".format(p.x, p.y) for p in bounding_box])


def return_first_word_from_the_string(input_string):
    string_words = input_string.split()
    first_word=string_words[0]
    return first_word

printable_letters = []
# The printable charcters are only in between values 32 to 127
for i in range(32,127):
    printable_letters.append(chr(i))

def filter_out_unprintable_words_from_string(input_string):
    string_words = input_string.split()
    output_string_list = []
    words_to_remove = []
    
    for word in string_words:
        for letter in word:
            if letter not in printable_letters:
                remove_word = True
                break
            else:
                remove_word = False
                
        if remove_word == True:
            words_to_remove.append(word)             
    
    output_string = input_string
    for word in words_to_remove:
        output_string = output_string.replace(word,"")
    
    output_string = output_string[1:] if (output_string[0]==" ") else output_string 
    output_string = output_string[:-1] if (output_string[-1]==" ") else output_string 
    return output_string


# Function to return the output of full document Analysis
def azure_complete_invoice_analysis(endpoint,key,document_analysis_client, invoiceUrl=False, invoicePath =False):
    # create your `DocumentAnalysisClient` instance and `AzureKeyCredential` variable
    with open(invoicePath,"rb") as file_pointer: 
        poller = document_analysis_client.begin_analyze_document("prebuilt-invoice",file_pointer)
    
    # Exterracting the text from the document
    invoices = poller.result()

    if invoices == None:
        return []
    
    #print("\n\n RAW INVOICE TEXT EXTRATION OUTPUT:\n\n",invoices)
    
    #print("\n\n The invoice documents are: ", invoices.documents)
    
    extracted_field_names =  []
    extracted_field_values = []
    extracted_field_confidence = []
    
    azure_general_head_field_to_field_name_map = {
        "VendorName":"vendor_name" ,
        "VendorAddress":"vendor_address" ,
        "VendorAddressRecipient": "vendor_address_recipient",
        "CustomerName":"customer_name",
        "CustomerId":"customer_id",
        "CustomerAddress":"customer_address",
        "CustomerAddressRecipient":"customer_address_recipient",
        "InvoiceId": "invoice_number",
        "InvoiceDate": "invoice_date",
        "InvoiceTotal": "total_amount",
        "DueDate": "payment_due_date",
        "PurchaseOrder": "purchase_order_number",
        "BillingAddress": "billing_address",
        "BillingAddressRecipient": "billing_address_recipient",
        "ShippingAddress": "shipping_address",
        "ShippingAddressRecipient": "shipping_address_recipient",
    }
    
    # To extract from item in invoice.fields.get("Items").value as item.value.get(item_field_name)
    azure_invoice_item_field_to_field_name_map = {
        "Description":  "description",
        "Quantity": "quantity",
        "Unit":"unit",
        "Unit Price":"unit_price",
        "ProductCode":"product_code",
        "Date":"date",
        "Tax":"tax",
        "Amount":"amount"
        
    }
    2   
    azure_general_tail_field_to_field_name_map = {
        "SubTotal": "amount",
        "TotalTax": "tax",
        "PreviousUnpaidBalance":"previous_unpaid_balance",
        "AmountDue": "total_due_amount",
        "ServiceStartDate": "service_start_date",
        "ServiceEndDate": "service_end_date",
        "ServiceAddress": "service_address",
        "ServiceAddressRecipient": "service_address_recipient",
        "RemittanceAddress": "remittance_address",
        "RemittanceAddressRecipient": "remittance_address_recipient"
          
    }
    
    amount_fields = ["InvoiceTotal", "Unit Price", "Tax","Amount", "SubTotal", "TotalTax", "PreviousUnpaidBalance", "AmountDue"]
    date_fields = ["InvoiceDate","DueDate", "Date", "ServiceStartDate"]

    if invoices.documents == None:
        return []

    for idx, invoice in enumerate(invoices.documents):
        # Extracting the Invoice Details in the Head  of the Invoice 
        
        for field_name in list(azure_general_head_field_to_field_name_map.keys()):
            if invoice.fields.get(field_name) != None:
                field = invoice.fields.get(field_name)
                if field:
                    if field.value!=None:
                        if field_name in amount_fields:
                            if field.value.symbol == "₹":
                                symbol = "Rs. "
                            else:
                                symbol = field.value.symbol
                            amount = str(field.value.amount) 
                            
                            extracted_field_values.append(amount)
                        elif field_name in date_fields:
                            extracted_field_values.append(field.value.strftime("%d-%m-%Y"))
                        else:
                            extracted_field_values.append(field.value)
                        extracted_field_names.append(azure_general_head_field_to_field_name_map[field_name])
                        extracted_field_confidence.append(field.confidence)
        
                    
        # Extracting the Details about individual Items in the Invoice
        if invoice.fields.get("Items") != None:
            for idx, item in enumerate(invoice.fields.get("Items").value):
                #print("\n\n...Item #{}".format(idx + 1))
                for item_field_name in list(azure_invoice_item_field_to_field_name_map.keys()):
                    if item.value.get(item_field_name) != None:
                        item_field = item.value.get(item_field_name)
                        
                        if item_field:
                            if item_field.value!=None:
                                if item_field_name in amount_fields:
                                    if item_field.value.symbol == "₹":
                                        symbol = "Rs. "
                                    else:
                                        symbol = item_field.value.symbol
                                    amount = str(item_field.value.amount)
                                    extracted_field_values.append(amount)
                                elif item_field_name in date_fields:
                                    extracted_field_values.append(item_field.value.strftime("%d-%m-%Y"))
                                else:  
                                    extracted_field_values.append(item_field.value)
                                extracted_field_names.append("Item_"+str(idx+1)+"_"+azure_invoice_item_field_to_field_name_map[item_field_name])
                                extracted_field_confidence.append(item_field.confidence)
                    
        #Extracting the details in the tail of the ijnvoice
        
        for field_name in list(azure_general_tail_field_to_field_name_map.keys()):
            if invoice.fields.get(field_name) != None:
                field = invoice.fields.get(field_name)
                if field:
                    if field.value!=None:
                        if field_name in amount_fields:
                            if field.value.symbol == "₹":
                                symbol = "Rs. "
                            else:
                                symbol = field.value.symbol
                            amount = str(field.value.amount) 
                            extracted_field_names.append(azure_general_tail_field_to_field_name_map[field_name])
                            extracted_field_values.append(amount)
                        elif field_name in date_fields:
                            extracted_field_values.append(field.value.strftime("%d-%m-%Y"))
                            extracted_field_names.append(azure_general_tail_field_to_field_name_map[field_name])
                        else:
                            extracted_field_values.append(field.value)
                            extracted_field_names.append(azure_general_tail_field_to_field_name_map[field_name])

                        extracted_field_confidence.append(field.confidence)
                
                
        all_extracted_field_information = []
        index = 0
        for key in extracted_field_names:
            field_info = dict()
            field_info['Field'] = key.lower()
            extracted_field_values[index] = filter_out_unprintable_words_from_string(extracted_field_values[index]) if isinstance(extracted_field_values[index], str) else extracted_field_values[index]
            if key in ["invoice_number", "purchase_order_number"]:
                field_info['Value'] = return_first_word_from_the_string(extracted_field_values[index])
            else:
                field_info['Value'] = extracted_field_values[index]
            field_info['Confidence'] = extracted_field_confidence[index]
            all_extracted_field_information.append(field_info)
            index+=1
        
        return all_extracted_field_information    
    
    
