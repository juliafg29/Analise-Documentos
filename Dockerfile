FROM python:3.11

WORKDIR /app

# System dependencies:
# - libgl1 + libglib2.0-0: required by opencv-python
# - tesseract-ocr: required by pytesseract
# - poppler-utils: required by pdf2image
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    ccache \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]