import streamlit as st
import os
from main import load_or_create_faceset, register_user
from PIL import Image

def main():
    st.title("Face Recognition Registration System")
    st.write("Upload a photo to register a new user")

    # Initialize session state for faceset data
    if 'faceset_data' not in st.session_state:
        st.session_state.faceset_data = load_or_create_faceset()
        
    # File uploader
    uploaded_file = st.file_uploader("Choose an image file", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_container_width=True)
        
        # Save uploaded file temporarily
        temp_path = os.path.join("temp", uploaded_file.name)
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Registration button
        if st.button("Register Face"):
            with st.spinner('Processing...'):
                # Call registration function
                result = register_user(temp_path, st.session_state.faceset_data)
                
                # Display result with appropriate styling
                if "successful" in result:
                    st.success(result)
                elif "Error" in result:
                    st.error(result)
                else:
                    st.warning(result)
            
            # Clean up temporary file
            os.remove(temp_path)
    
    # Display registered users count
    if st.session_state.faceset_data and 'user_tokens' in st.session_state.faceset_data:
        st.sidebar.metric(
            "Registered Users", 
            len(st.session_state.faceset_data['user_tokens'])
        )

if __name__ == "__main__":
    main()