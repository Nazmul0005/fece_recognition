import requests
import json
import os

API_KEY = ''      # Your Face++ API key
API_SECRET = ''  # Your Face++ API secret

# Add this function to handle faceset token persistence
def load_or_create_faceset():
    token_file = 'faceset_token.json'
    
    # Initialize default structure
    default_data = {
        'faceset_token': None,
        'user_tokens': []
    }
    
    # Try to load existing data
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            try:
                data = json.load(f)
                # Ensure backwards compatibility
                if 'user_tokens' not in data:
                    data['user_tokens'] = []
                return data
            except json.JSONDecodeError:
                return default_data
    
    # If no file exists, create new faceset
    faceset_token = create_face_set()
    if faceset_token:
        default_data['faceset_token'] = faceset_token
        with open(token_file, 'w') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    return default_data

def create_face_set():
    url = 'https://api-us.faceplusplus.com/facepp/v3/faceset/create'
    data = {
        'api_key': API_KEY,
        'api_secret': API_SECRET,
        'display_name': 'UserFaceSet'  # Name your face set
    }
    response = requests.post(url, data=data)
    
    # Check status code before parsing JSON
    if response.status_code != 200:
        print(f"Error creating face set: Status code {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    try:
        result = response.json()
        if 'faceset_token' in result:
            print("Face set created. Token:", result['faceset_token'])
            return result['faceset_token']
        else:
            print("Failed to create face set:", result)
            return None
    except requests.exceptions.JSONDecodeError:
        print("Error: Unable to parse JSON response from create_face_set")
        print(f"Response: {response.text}")
        return None

def save_user_token(face_token):
    token_file = 'faceset_token.json'
    try:
        with open(token_file, 'r') as f:
            data = json.load(f)
        
        # Add new token if not already present
        if face_token not in data['user_tokens']:
            data['user_tokens'].append(face_token)
            
        with open(token_file, 'w') as f:
            json.dump(data, f, indent=4)
            
        return True
    except Exception as e:
        print(f"Error saving user token: {str(e)}")
        return False

def register_user(image_path, faceset_data):
    # Get faceset token from data
    faceset_token = faceset_data['faceset_token']
    
    # Step 1: Detect the face in the image
    detect_url = 'https://api-us.faceplusplus.com/facepp/v3/detect'
    try:
        files = {'image_file': open(image_path, 'rb')}
    except FileNotFoundError:
        return "Error: Image file not found at the specified path"
    
    data = {
        'api_key': API_KEY,
        'api_secret': API_SECRET
    }
    response = requests.post(detect_url, files=files, data=data)
    
    # Check if the API call was successful
    if response.status_code != 200:
        print(f"Error detecting face: Status code {response.status_code}")
        print(f"Response: {response.text}")
        return "Error: Failed to detect face"
    
    # Try to parse the JSON response
    try:
        result = response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Unable to parse JSON response from detect endpoint")
        print(f"Response: {response.text}")
        return "Error: Invalid response from API"
    
    # Check for face detection issues
    if 'faces' not in result or len(result['faces']) == 0:
        return "Error: No face detected in the image"
    elif len(result['faces']) > 1:
        return "Error: Multiple faces detected in the image"
    
    face_token = result['faces'][0]['face_token']
    
    # Check if user already exists in our local storage
    if face_token in faceset_data['user_tokens']:
        return "Error: This user is already registered"
    
    # Step 2: Search for duplicates in the face set
    search_url = 'https://api-us.faceplusplus.com/facepp/v3/search'
    data = {
        'api_key': API_KEY,
        'api_secret': API_SECRET,
        'face_token': face_token,
        'faceset_token': faceset_token,
        'return_result_count': 1  # Return the top match
    }
    response = requests.post(search_url, data=data)
    
    if response.status_code != 200:
        try:
            error_json = response.json()
            if 'error_message' in error_json and error_json['error_message'] == 'EMPTY_FACESET':
                print("First registration in empty faceset - proceeding with face addition")
            else:
                print(f"Error searching for duplicates: Status code {response.status_code}")
                print(f"Response: {response.text}")
                return "Error: Failed to search for duplicates"
        except:
            return "Error: Failed to search for duplicates"
    
    try:
        result = response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Unable to parse JSON response from search endpoint")
        print(f"Response: {response.text}")
        return "Error: Invalid response from API"
    
    # Step 3: Check for duplicates
    if 'results' in result and len(result['results']) > 0:
        confidence = result['results'][0]['confidence']
        print(f"Face match confidence: {confidence}%")  # Debug info
        if confidence > 70:  # Lower threshold for stricter matching
            return f"Duplicate face detected with {confidence}% confidence. Registration denied."
    
    # Step 4: No duplicate, add the face to the face set
    add_url = 'https://api-us.faceplusplus.com/facepp/v3/faceset/addface'
    data = {
        'api_key': API_KEY,
        'api_secret': API_SECRET,
        'faceset_token': faceset_token,
        'face_tokens': face_token
    }
    response = requests.post(add_url, data=data)
    
    if response.status_code == 200:
        if save_user_token(face_token):
            return "Registration successful. Face added to the set."
        else:
            return "Registration successful but failed to save user token."
    else:
        print(f"Error adding face: Status code {response.status_code}")
        print(f"Response: {response.text}")
        return "Error: Failed to add face to the set."

if __name__ == "__main__":
    # Load existing or create new faceset data
    faceset_data = load_or_create_faceset()
    
    if faceset_data['faceset_token']:
        result = register_user('D:\AAAA_SM_Project\Face_recognition\IMG_20250331_1032232.jpg', faceset_data)
        print(result)
    else:
        print("Cannot proceed with registration due to face set creation failure.")