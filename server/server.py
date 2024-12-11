import os
import boto3
import openai
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    # Ensure these are set as environment variables or in a secure configuration
    UPLOAD_FOLDER = 'uploads/'
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    ALLOWED_TEMPLATE_EXTENSIONS = {'xls', 'xlsx'}
    
    # AWS Textract and S3 Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def extract_text_with_textract(file_path):
    print("textract here")
    """
    Extract text from document using AWS Textract
    
    Args:
        file_path (str): Path to the document file
    
    Returns:
        str: Extracted text from the document
    """
    # Initialize Textract client
    textract = boto3.client(
        'textract', 
        region_name=Config.AWS_REGION,
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
    )

    
    # Read document content
    with open(file_path, 'rb') as document:
        response = textract.detect_document_text(Document={'Bytes': document.read()})
    
    # Combine detected text
    detected_text = []
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            detected_text.append(item['Text'])

    print('\n'.join(detected_text))
    
    return '\n'.join(detected_text)

def generate_excel_data_with_openai(extracted_text, template_path):
    """
    Use OpenAI to populate Excel template based on extracted text
    
    Args:
        extracted_text (str): Text extracted from the document
        template_path (str): Path to the Excel template
    
    Returns:
        pd.DataFrame: Populated DataFrame
    """
    # Initialize OpenAI client
    openai.api_key = Config.OPENAI_API_KEY
    
    # Read Excel template to get column names
    template_df = pd.read_excel(template_path, sheet_name=0, header=0)
    column_names = template_df.columns.tolist()

    
    # Prepare prompt for OpenAI
    prompt = f"""
    Given the following extracted document text:
    {extracted_text}
    
    Please fill in the following Excel columns with appropriate data:
    {column_names}
    
    Respond with a JSON-formatted object where keys are column names and values are the corresponding data.
    """
    
    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from documents."},
                {"role": "user", "content": prompt}
            ],
        )
        
        # Parse the response
        response_content = response['choices'][0]['message']['content']
        
        # Parse the JSON response content
        data_dict = json.loads(response_content)
        
        # Create DataFrame from extracted data
        result_df = pd.DataFrame([data_dict])
        
        return result_df
    
    except Exception as e:
        print(f"Error in OpenAI processing: {e}")
        return None

@app.route('/api/process-document', methods=['POST'])
def process_document():
    """
    Main API endpoint for document processing
    """
    print("test")
    # Check if files are present
    if 'document' not in request.files or 'template' not in request.files:
        return jsonify({"error": "Missing document or template file"}), 400
    
    document = request.files['document']
    template = request.files['template']
    
    # Validate file types
    if not document or not allowed_file(document.filename, Config.ALLOWED_DOCUMENT_EXTENSIONS):
        return jsonify({"error": "Invalid document file"}), 400
    
    if not template or not allowed_file(template.filename, Config.ALLOWED_TEMPLATE_EXTENSIONS):
        return jsonify({"error": "Invalid template file"}), 400
    
    try:
        # Save files
        document_path = os.path.join(Config.UPLOAD_FOLDER, secure_filename(document.filename))
        template_path = os.path.join(Config.UPLOAD_FOLDER, secure_filename(template.filename))
        
        document.save(document_path)
        template.save(template_path)
        
        # Extract text using Textract
        # extracted_text = extract_text_with_textract(document_path)
        extracted_text= 'test'
        
        # Generate Excel data using OpenAI
        result_df = generate_excel_data_with_openai(extracted_text, template_path)
        
        if result_df is None:
            return jsonify({"error": "Failed to process document"}), 500
        
        # Save processed file
        output_path = os.path.join(Config.UPLOAD_FOLDER, 'processed_template.xlsx')
        result_df.to_excel(output_path, index=False)
        
        # Optional: Return download URL or file
        return send_file(
            output_path, 
            as_attachment=True, 
            download_name='processed_document.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     # Clean up temporary files
    #     try:
    #         if os.path.exists(document_path):
    #             os.remove(document_path)
    #         if os.path.exists(template_path):
    #             os.remove(template_path)
    #         if os.path.exists(output_path):
    #             os.remove(output_path)
        # except:
        #     pass

if __name__ == '__main__':
    app.run(debug=True)

# Requirements file (requirements.txt)
# Flask==2.1.0
# flask-cors==3.0.10
# boto3==1.26.137
# openai==0.27.0
# pandas==1.5.3
# openpyxl==3.1.2