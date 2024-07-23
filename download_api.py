import json
import io
import base64
from flask import Flask, request, jsonify, send_file
from flask.logging import create_logger
import requests
import serverless_wsgi

# Configuración
CLIENT_ID = ''
CLIENT_SECRET = ''
TENANT_ID = ''
SCOPE = 'https://graph.microsoft.com/.default'
DRIVE_ID = ''

app = Flask(__name__)
logger = create_logger(app)

def get_access_token():
    token_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': SCOPE
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json().get('access_token')

def list_file_ids(access_token, drive_id):
    list_files_url = f'https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(list_files_url, headers=headers)
    response.raise_for_status()
    result = response.json()
    
    files = result.get('value', [])
    return {file['name']: file['id'] for file in files}

def get_file_id_by_name(file_ids, file_name):
    file_id = file_ids.get(file_name)
    if file_id:
        return file_id
    else:
        raise FileNotFoundError(f'Archivo con nombre {file_name} no encontrado')

def download_file(access_token, drive_id, file_id):
    download_url = f'https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{file_id}/content'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(download_url, headers=headers)
    response.raise_for_status()
    return response.content

@app.route('/download', methods=['GET'])
def download_file_route():
    try:
        access_token = get_access_token()
        
        file_name = request.args.get('file_name')
        if not file_name:
            return jsonify({'error': 'File name not provided'}), 400

        file_ids = list_file_ids(access_token, DRIVE_ID)
        file_id = get_file_id_by_name(file_ids, file_name)
        file_content = download_file(access_token, DRIVE_ID, file_id)
        
        return send_file(
            io.BytesIO(file_content),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=file_name
        )
    except FileNotFoundError as e:
        logger.error(f'File not found: {str(e)}')
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f'Error during file download: {str(e)}')
        return jsonify({'error': str(e)}), 500

def lambda_handler(event, context):
    if 'headers' not in event:
        event['headers'] = event.get('params', {}).get('header', {})
    
    if 'path' not in event:
        event['path'] = event.get('context', {}).get('resource-path', '')
    
    if 'httpMethod' not in event:
        event['httpMethod'] = event.get('context', {}).get('http-method', '')

    response = serverless_wsgi.handle_request(app, event, context)

    # Adjust response to ensure binary content is properly handled
    if 'Content-Disposition' in response['headers']:
        response['isBase64Encoded'] = True
        response['body'] = base64.b64encode(response['body'].encode()).decode()

    return response

if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=True)
