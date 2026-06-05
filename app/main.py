from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
from pathlib import Path
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
    arquivo: UploadFile = File(...),
    tipo_entrada: str = Form("documento_escaneado"),
    pasta_saida: str = Form(".")
):
    caminho_temporario = None

    try:
        tipo_entrada = tipo_entrada.strip().lower()
        tipos_validos = ["cnh_digital", "documento_escaneado"]

        if tipo_entrada not in tipos_validos:
            raise HTTPException(
                status_code=400,
                detail="tipo_entrada inválido. Use 'cnh_digital' ou 'documento_escaneado'."
            )

        if not arquivo.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Somente PDF é permitido."
            )

        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

        conteudo = await arquivo.read()

        if len(conteudo) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Arquivo muito grande."
            )

        if not conteudo.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Arquivo PDF inválido."
            )

        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(conteudo)
            caminho_temporario = temp_file.name

        print(f"[debug] Tipo de entrada informado: {tipo_entrada}\n")

        ocr_paddleocr = None

        if tipo_entrada == "documento_escaneado":
            print("[debug] Vai compor Paddle OCR...\n")
            ocr = utils.compose_paddle_ocr()
        else:
            ocr = "Pytesseract"
            print("[debug] Documento informado como CNH digital. Paddle OCR não será carregado.\n")

        print("[debug] Vai processar o documento...\n")

        resultado = document_workflow(
            input_file_path=caminho_temporario,
            tipo_entrada=tipo_entrada,
            ocr=ocr
        )

        print("[debug] Terminou document_workflow.\n")

        # Cria a pasta de saída, se ela não existir
        pasta_saida = Path(pasta_saida)
        pasta_saida.mkdir(parents=True, exist_ok=True)

        # Define nome do XML com base no nome original do PDF
        nome_base = Path(arquivo.filename).stem
        caminho_xml = pasta_saida / f"{nome_base}_resultado.xml"

        # Pega o XML final gerado
        xml_final = resultado.get("xml")

        if not xml_final:
            raise HTTPException(
                status_code=500,
                detail="O XML final não foi encontrado no resultado do processamento."
            )

        # Salva o XML na pasta de saída
        caminho_xml.write_text(xml_final, encoding="utf-8")

        print(f"[debug] XML salvo em: {caminho_xml}\n")

        return JSONResponse(content={
            "status": "sucesso",
            "tipo_entrada": tipo_entrada,
            "arquivo_xml": str(caminho_xml),
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