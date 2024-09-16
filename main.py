from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.staticfiles import StaticFiles
from pdf_utils import extract_text_from_pdf, fitz
import re, openai, os 
import spacy


# Database setup
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CVData(Base):
    __tablename__ = "cv_data"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)  # Added address column
    gender = Column(String, nullable=True)
    education = Column(String, nullable=True)
    training = Column(String, nullable=True)  # Added training column
    skills = Column(String, nullable=True)
    experience = Column(String, nullable=True)
    languages = Column(String, nullable=True)




Base.metadata.create_all(engine)


openai.api_key = "yosk-proj-XA2OUOVqfc54TVek3GUwuIdku0l0usaO9Dyx6rF3UTzH_Tb1zYI55Crj6GkT3AuUG8c2hYnhJtT3BlbkFJrfCn0VlTir9CPBHpuUO5btNasTPJOhUpk5HCPt2V6Cdnc157tkqrtdUfCaHol6LHNs5q5_PYkA"

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

nlp = spacy.load("en_core_web_sm")



def extract_details(text: str):
    # General regex patterns for common fields
    patterns = {
        "email": r"[\w\.-]+@[\w\.-]+",
        "phone_number": r"\+?\d{1,3}[\s-]?\(?\d+\)?[\s-]?\d+[\s-]?\d+",  # Covers international formats
        "gender": r"(Male|Female|Other|Gender[:\s]+(Male|Female|Other))",  # Detect gender
        "education": r"(?i)(Education|Academic Qualifications|Degrees)[\s\S]+?(?=\n[A-Z])",  # Until a new section
        "skills": r"(?i)(Skills|Technical Skills)[\s\S]+?(?=\n[A-Z])",  # Until a new section
        "experience": r"(?i)(Experience|Work Experience|Professional Experience)[\s\S]+?(?=\n[A-Z])",  # Until a new section
        "training": r"(?i)(Training|Certifications)[\s\S]+?(?=\n[A-Z])",  # Until a new section
        "languages": r"(?i)(Languages|Proficiency)[\s\S]+?(?=\n[A-Z])",  # Until a new section
    }

    # Initialize dictionary for storing extracted details
    details = {"name": None, "email": None, "phone_number": None, "education": None,
               "skills": None, "experience": None,"gender":None, "training": None, "languages": None}

    # Use spaCy NER for name extraction
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not details["name"]:
            details["name"] = ent.text

    # Extract details based on patterns
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if key == "gender":
                details[key] = match.group(1)
            else:
                details[key] = match.group().strip()

    return details

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return templates.TemplateResponse("upload.html", {"request": {}})


@app.post("/upload/", response_class=HTMLResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")
    
    # Save the uploaded file temporarily
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())

# Extract text from PDF
    text = ""
    try:
        doc = fitz.open(file_location)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF.")
    
    # Extract details
    details = extract_details(text)

    # Save to the database
    db_item = CVData(
        name=details["name"],
        email=details["email"],
        phone_number=details["phone_number"],
        gender=details["gender"],
        education=details["education"],
        languages=details["languages"],
        skills=details["skills"],
        experience=details["experience"],
        training=details["training"]
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return templates.TemplateResponse("result.html", {"request": {}, "details": details})

# @app.post("/upload/", response_class=HTMLResponse)
# async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
#     if file.content_type != 'application/pdf':
#         raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")
    
#     # Save the uploaded file temporarily
#     file_location = f"temp_{file.filename}"
#     with open(file_location, "wb") as f:
#         f.write(file.file.read())

#     # Extract text from the uploaded PDF
#     text = extract_text_from_pdf(file_location)

#     # Extract details using OpenAI
#     details = extract_details_using_openai(text)

#     # Save extracted details to the database
#     db_item = CVData(
#         name=details.get("name"),
#         email=details.get("email"),
#         phone_number=details.get("phone_number"),
#         gender=details.get("gender"),
#         education=details.get("education"),
#         languages=details.get("languages"),
#         skills=details.get("skills"),
#         experience=details.get("experience"),
#         training=details.get("training")
#     )
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)

#     # Remove the temporary file after processing
#     os.remove(file_location)

#     # Return the details in the template
#     return templates.TemplateResponse("result.html", {"request": {}, "details": details})

@app.get("/view", response_class=HTMLResponse)
async def view_data(request: Request, db: Session = Depends(get_db)):
    # Fetch data from the database
    cv_entries = db.query(CVData).all()
    
    return templates.TemplateResponse("view.html", {"request": request, "cv_entries": cv_entries})
