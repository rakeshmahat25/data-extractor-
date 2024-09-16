import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

# from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
# import openai
# import pdfplumber


# def extract_details_using_openai(text):
#     prompt = f"""
#     Extract the following details from the CV text provided:
    
#     1. Name
#     2. Email
#     3. Phone Number
#     4. Education
#     5. Skills
#     6. Experience
#     7. Gender
#     8. Training
#     9. Languages

#     CV Text:
#     {text}
#     """
    
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",  # or "gpt-3.5-turbo" if you are using GPT-3.5
#         messages=[
#             {"role": "system", "content": "You are an assistant that extracts CV details."},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0,
#         max_tokens=500,
#     )
    
#     return response['choices'][0]['message']['content'].strip()

# # Function to extract text from PDF using pdfplumber
# def extract_text_from_pdf(file_path):
#     text = ""
#     try:
#         with pdfplumber.open(file_path) as pdf:
#             for page in pdf.pages:
#                 text += page.extract_text() + "\n"
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Failed to extract text from PDF.")
    
#     return text
