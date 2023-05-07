import streamlit as st
import requests
import uuid
import io
import os
import spacy
from spacy import displacy
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import time
import json

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
connection_string = "DefaultEndpointsProtocol=https;AccountName=diginoticeocr;AccountKey=KNQF2HZB62WiXPUtg/rxbVxJn8yCQS6oTc4o+J2mFp0uL5is2j4pZsgZoOy7rO3cbsmfTxWSRL3b+AStT7nJ9A==;EndpointSuffix=core.windows.net"
container_name = "notices"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)


# Define the correct username and password as environment variables
CORRECT_USERNAME ="Mahesh"
CORRECT_PASSWORD = "74"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Function to perform OCR using pytesseract
def perform_ocr(image_stream):
    subscription_key1 = "bd1854170fe4480db767b56052e29edc"
    endpoint1 = "https://digiocrcomputervision.cognitiveservices.azure.com/"

    computervision_client = ComputerVisionClient(endpoint1, CognitiveServicesCredentials(subscription_key1))
    read_response = computervision_client.read_in_stream(
        image=image_stream,
        mode="Printed",
        raw=True
    )

    # Get the operation location (URL with an ID at the end) from the response
    read_operation_location = read_response.headers["Operation-Location"]
    # Grab the ID from the URL
    operation_id = read_operation_location.split("/")[-1]

    # Call the "GET" API and wait for it to retrieve the results
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)
    text = " "
    # Print the detected text, line by line
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                texts = line.text
                text = text + " " + texts
    return text


# Function to translate Marathi text to English using Googletrans library
def translate_text(text, source_language, target_language):
    endpoint = "https://api.cognitive.microsofttranslator.com/"
    location = "centralindia"
    subscription_key = "f50f0f20cc6b4c4b87e71e62fe7b7ffd"
    path = '/translate'
    params = {
        'api-version': '3.0',
        'from': 'mr',
        'to': 'en'
    }
    constructed_url = endpoint + path

    # Prepare request headers
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Prepare request body
    body = [{
        'text': text
    }]

    # Call Azure Translation API
    response = requests.post(constructed_url, headers=headers, json=body, params=params)
    response_data = response.json()
    if 'error' in response_data:
        return f"Error: {response_data['error']['message']}"
    if 'translations' in response_data[0]:
        return response_data[0]['translations'][0]['text']
    else:
        return f"Error: Translation not found in response: {response_data}"
    return response_data[0]['translations'][0]['text']


# Streamlit app
def main():
    # Set app title and description
    st.set_page_config(page_title='Marathi Text OCR and Translation', page_icon=':memo:', layout='wide')
    st.title('ODA OCR and Translation')

    # Add login functionality
    if st.session_state.authenticated:
        # Upload images
        uploaded_files = st.file_uploader('Upload image files', accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

        if uploaded_files:
            with st.spinner('Performing OCR and translation...'):
                # Iterate over uploaded images
                for uploaded_file in uploaded_files:
                    # Open the image
                    image_stream = io.BytesIO(uploaded_file.read())

                    # Perform OCR
                    text = perform_ocr(image_stream)


                    st.header("Uploaded Image")
                    st.image(uploaded_file, use_column_width=True)

                    st.header("Marathi OCR Text")
                    st.write(text)

                    # Initialize SpaCy model
                    nlp = spacy.load("C:/Users/MaheshRaval/Mahesh/Practice Project/Resume Parsing/Diginotice/trained_model_colab/MarathiModels/MarathiFinal")
                    # Perform NER using custom trained SpaCy model
                    doc = nlp(text)



                    st.header("Visualization of Predicted Fields")
                    html = displacy.render(doc, style='ent')
                    st.markdown(html, unsafe_allow_html=True)
                    entities = [(ent.text, ent.label_) for ent in doc.ents]
                    #st.write(entities)

                    st.header("Predicted Marathi Entities:")
                    res = []
                    for entity in entities:
                        st.write(entity)
                        res.append(entity)

                    st.header("Translated Results in English:")
                    translated_dict = {}
                    for entity in entities:
                        marathi_text = entity[0]
                        entity_type = entity[1]
                        english_text = translate_text(marathi_text,'mr', 'en')
                        st.write(f"('{english_text}' : '{entity_type} ')")
                        translated_dict[entity_type] = english_text

                    # Print the translated dictionary in the specified format
                    #json_output = json.dumps(translated_dict, ensure_ascii=False, indent=4)
                    #st.write(json_output)





    else:

        # Add login form

        username = st.sidebar.text_input('Username')

        password = st.sidebar.text_input('Password', type='password')

        if st.sidebar.button('Login', key='login_button'):

            if username == CORRECT_USERNAME and password == CORRECT_PASSWORD:

                st.session_state.authenticated = True

                st.success('Logged in successfully.')

                st.button('Click here to Upload files')

            else:

                st.error('Incorrect username or password')

if __name__ == '__main__':
    main()