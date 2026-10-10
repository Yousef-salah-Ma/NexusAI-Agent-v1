from fastapi import (
    FastAPI, Depends, HTTPException,
    UploadFile, File, Form
)
from typing import Optional
from pypdf import PdfReader
from io import BytesIO
from model import model_app
from sec import  get_current_user
from pathlib import Path
from fastapi.responses import FileResponse
from tools import REPORTS_DIR
from schame import login_users , Create_Account , messegas 
from auth import Register ,login

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/Register")
def Register_user(data : Create_Account):
   

    return Register( FirstName=data.FirstName,
            LastName=data.LastName,
            age=data.age,
            email=data.email,
            password=data.password )


@app.post("/login")
def login_user(data : login_users):
    return login(data.password , data.email)



@app.get("/download/{filename}", name="download_report")
def download_report(
    filename: str,
    user: dict = Depends(get_current_user)
):
    # منع استخدام اسم الملف للوصول لمسارات أخرى
    if Path(filename).name != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    root = REPORTS_DIR.resolve()
    file_path = (root / filename).resolve()

    if file_path.parent != root or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )

@app.post("/chat")
async def chat(
    message: str = Form(...),
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    user_id = str(user)

    content = message

    if file is not None:
        data = await file.read()

        if file.content_type == "application/pdf":
            reader = PdfReader(BytesIO(data))
            extracted_text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        elif (
            file.content_type == "text/plain"
            or file.filename.lower().endswith(".txt")
        ):
            extracted_text = data.decode("utf-8-sig")

        else:
            raise HTTPException(
                status_code=415,
                detail="Only PDF and TXT files are supported"
            )

        content += "\n\nFile content:\n" + extracted_text
 
    if image is not None:
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=415,
                detail="Please upload a valid image"
            )

        image_data = await image.read()

        import base64

        encoded_image = base64.b64encode(
            image_data
        ).decode("utf-8")

        content = [
            {
                "type": "text",
                "text": content
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": (
                        f"data:{image.content_type};"
                        f"base64,{encoded_image}"
                    )
                }
            }
        ]


    result = model_app(
        content=content,
        thread_id=user_id
    )

    download_url = None

    if result["report"] is not None:
        filename = result["report"]["file_name"]
        download_url = f"/download/{filename}"

    return {
        "user_id": user_id,
        "response": result["answer"],
        "download_url": download_url
    }
