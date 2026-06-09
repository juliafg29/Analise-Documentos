from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
from pathlib import Path
import os

from app.services.document_workflow import document_workflow
import app.services.utils as utils

app = FastAPI(
    title="Serviço de Validação e Extração de Dados de Documentos Pessoais",
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

    logger = utils.configurar_logger(pasta_saida)

    try:
        logger.info("Iniciando análise do documento")
        logger.info(f"Arquivo recebido: {arquivo.filename}")
        logger.info(f"Tipo de entrada informado: {tipo_entrada}")


        tipo_entrada = tipo_entrada.strip().lower()
        tipos_validos = ["cnh_digital", "documento_escaneado"]

        if tipo_entrada not in tipos_validos:
            logger.error(f"Tipo de entrada inválido: {tipo_entrada}")
            raise HTTPException(
                status_code=400,
                detail="tipo_entrada inválido. Use 'cnh_digital' ou 'documento_escaneado'."
            )

        if not arquivo.filename.lower().endswith(".pdf"):
            logger.error("Arquivo rejeitado: extensão diferente de PDF")
            raise HTTPException(
                status_code=400,
                detail="Somente PDF é permitido."
            )

        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

        conteudo = await arquivo.read()

        if len(conteudo) > MAX_FILE_SIZE:
            logger.error(f"Arquivo muito grande: {len(conteudo)} bytes")
            raise HTTPException(
                status_code=413,
                detail="Arquivo muito grande."
            )

        if not conteudo.startswith(b"%PDF-"):
            logger.error("Arquivo rejeitado: conteúdo não inicia com assinatura PDF")
            raise HTTPException(
                status_code=400,
                detail="Arquivo PDF inválido."
            )

        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(conteudo)
            caminho_temporario = temp_file.name

        ocr_paddleocr = None

        if tipo_entrada == "documento_escaneado":
            logger.info("Documento escaneado informado. PaddleOCR será carregado.")
            ocr = utils.compose_paddle_ocr()
        else:
            ocr = "Pytesseract"
            logger.info("CNH digital informada. Pytesseract será carregado.")

        resultado = document_workflow(
            input_file_path=caminho_temporario,
            tipo_entrada=tipo_entrada,
            ocr=ocr
        )

        # Cria a pasta de saída, se ela não existir
        pasta_saida = Path(pasta_saida)
        pasta_saida.mkdir(parents=True, exist_ok=True)

        # Define nome do XML com base no nome original do PDF
        nome_base = Path(arquivo.filename).stem
        caminho_xml = pasta_saida / f"{nome_base}_resultado.xml"

        # Pega o XML final gerado
        xml_final = resultado.get("xml")

        if not xml_final:
            logger.error("XML final não encontrado no resultado")
            raise HTTPException(
                status_code=500,
                detail="O XML final não foi encontrado no resultado do processamento."
            )

        # Salva o XML na pasta de saída
        caminho_xml.write_text(xml_final, encoding="utf-8")

        logger.info(f"Arquivo XML com informações completas salvo em: {caminho_xml.resolve()}")

        return JSONResponse(content={
            "status": "sucesso",
            "tipo_entrada": tipo_entrada,
            "arquivo_xml": str(caminho_xml),
            "resultado": resultado
        })

    except HTTPException:
        raise

    except Exception as erro:
        logger.exception(f"Erro ao processar documento: {str(erro)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar documento: {str(erro)}"
        )

    finally:
        if caminho_temporario and os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)
            logger.info(f"Arquivo temporário removido: {caminho_temporario}")