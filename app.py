import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from flask import Flask,jsonify,request, render_template
from werkzeug.utils import secure_filename
#from flask_restful import Resource, Api
from azure_invoice_information_extraction_module import *
#from flask_ngrok import run_with_ngrok
import requests
import boto3

# Azure FormRecognizer Configuration Information
# Organization endpoint 

endpoint = "https://southeastasia.cognitiveservices.azure.com"
key = "bc3fedc9ef7545ee9d01b1e1accdb0c7"

s3 = boto3.resource('s3')

bucket =  s3.Bucket('gamilapi')

#endpoint = "https://zaggle-invoice-form-recognizer.cognitiveservices.azure.com/"
#key = "f8de20beed4641c2ba3b6307122bfa95"

# Initializing a Flask APP
app = Flask(__name__)
# Assigned the Flask app as an API
#api = Api(app)
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
#run_with_ngrok(app)


# Now we define a class which willl act as an API resource
document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    

@app.route('/')
def get_invoice_url():
    return render_template('get_invoice_s3_bucket_file_name.html')

@app.route('/', methods=['POST','GET'])
def azure_extract_invoice_information():
    if request.method =='POST':
        print("hello")
        invoice_file_name =  request.form['s3_bucket_file_name']
        if invoice_file_name:
            invoice_file_path = os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(invoice_file_name))
            bucket.download_file(invoice_file_name, invoice_file_path)
            invoice_extracted_information = azure_complete_invoice_analysis(endpoint=endpoint,key=key,invoicePath = invoice_file_path, document_analysis_client=document_analysis_client)
            #print(invoice_extracted_information)
            # Empty all files in the uploads folder
            for file in os.listdir(app.config['UPLOAD_FOLDER']):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))

            return jsonify(invoice_extracted_information)

