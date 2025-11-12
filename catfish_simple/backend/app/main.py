import json

from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_session
from .models import Upload
from .signal_pipeline import analyze_upload

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Catfish Check API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/uploads")
def list_uploads(session: Session = Depends(get_session)):
    uploads = session.query(Upload).order_by(Upload.created_at.desc()).limit(5).all()
    return [
        {
            "id": upload.id,
            "filename": upload.filename,
            "content_type": upload.content_type,
            "created_at": upload.created_at.isoformat(),
            "risk_score": upload.risk_score,
            "confidence": upload.confidence,
            "signals": json.loads(upload.signals) if upload.signals else [],
            "advice": json.loads(upload.advice) if upload.advice else [],
            "profile_url": upload.profile_url,
            "notes": upload.notes,
            "profile_bio": upload.profile_bio,
            "conversation_text": upload.conversation_text,
        }
        for upload in uploads
    ]


@app.post("/api/uploads", status_code=201)
async def upload_image(
    files: List[UploadFile] = File(...),
    profile_url: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    profile_bio: str | None = Form(default=None),
    conversation_text: str | None = Form(default=None),
    session: Session = Depends(get_session),
):
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")

    saved_uploads: List[Upload] = []
    for file in files:
        if not file.filename:
            continue
        contents = await file.read()
        analysis = analyze_upload(
            contents,
            profile_url,
            notes,
            profile_bio,
            conversation_text,
            session,
        )
        upload = Upload(
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            data=contents,
            profile_url=profile_url,
            notes=notes,
            profile_bio=profile_bio,
            conversation_text=conversation_text,
            phash=analysis["phash"],
            sha256=analysis["sha256"],
            risk_score=analysis["risk_score"],
            confidence=analysis["confidence"],
            signals=json.dumps(analysis["signals"]),
            advice=json.dumps(analysis["advice"]),
        )
        session.add(upload)
        session.flush()
        saved_uploads.append(upload)

    session.commit()

    response = []
    for upload in saved_uploads:
        response.append(
            {
                "id": upload.id,
                "filename": upload.filename,
                "content_type": upload.content_type,
                "created_at": upload.created_at.isoformat(),
                "risk_score": upload.risk_score,
                "confidence": upload.confidence,
                "signals": json.loads(upload.signals) if upload.signals else [],
                "advice": json.loads(upload.advice) if upload.advice else [],
                "profile_url": upload.profile_url,
                "notes": upload.notes,
                "profile_bio": upload.profile_bio,
                "conversation_text": upload.conversation_text,
            }
        )
    return {"uploads": response}
