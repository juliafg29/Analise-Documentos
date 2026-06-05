from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
import shutil
import os

from app.services.document_workflow import document_workflow
import app.services.utils as utils

app = FastAPI(
    title="Serviço de Validação e Extração de Documentos",
    description="API para validação, extração de dados e geração XML de documentos pessoais digitalizados.",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "mensagem": "API de processamento de documentos ativa."
    }


@app.post("/documentos/analisar")
async def analisar_documento(
    arquivo: UploadFile = File(...)
):
    caminho_temporario = None

    try:
        if not arquivo.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Somente PDF é permitido.")

        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

        conteudo = await arquivo.read()

        if len(conteudo) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Arquivo muito grande.")

        if not conteudo.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Arquivo PDF inválido.")

        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(conteudo)
            caminho_temporario = temp_file.name

        print("[debug] Vai compor Paddle ocr: .. \n")
            # 1. Compose Paddle OCR
        ocr_paddleocr = utils.compose_paddle_ocr()
            
        print("[debug] Vai processar o documento: .. \n")
        resultado = document_workflow(caminho_temporario, ocr_paddleocr)

        print("[debug] terminou do: .. \n")
        return JSONResponse(content={
            "status": "sucesso",
            "resultado": resultado
        })

    except HTTPException:
        raise

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar documento: {str(erro)}"
        )

    finally:
        if caminho_temporario and os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)  

'''
@app.post("/documentos/analisar")
async def analisar_documento(
    arquivo: UploadFile = File(...)
):
    """
    Endpoint responsável por:
    - receber um PDF
    - validar o documento
    - extrair dados
    - gerar XML
    """

    caminho_temporario = None

    # Verifica extensão
    if not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Somente PDF é permitido.")

    conteudo = await arquivo.read()

    if conteudo != b"%PDF-":
        raise HTTPException(status_code=400, detail="Arquivo PDF inválido.")

    #await arquivo.seek(0)

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    #conteudo = await arquivo.read()
    if len(conteudo) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande.")

    try:
        # Salva o arquivo temporariamente
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(conteudo)
            caminho_temporario = temp_file.name

        # Processa documento
        print("[debug] Vai processar o documento: .. \n")
        resultado = document_workflow(caminho_temporario)

        print("O resultado foi: " , resultado["xml"])
        
        return JSONResponse(content={
            "status": "sucesso",
            "resultado": resultado
        })

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar documento: {str(erro)}"
        )

    finally:
        # Remove arquivo temporário
        if caminho_temporario and os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)

'''