import app.services.utils as utils
from app.services.document_complete import analisar_documento_morfologia
from app.services.extract_digitalized_data import processar_documento
from app.services.extract_digital_cnh_data import extract_ecnh
from app.services.xml_utils import gerar_xml

from datetime import datetime
import logging



def document_workflow(input_file_path, tipo_entrada, ocr, MIN_SCORE = 0.5):

    logger = logging.getLogger("documento")

    # 1. PDF para Imagem
    all_image_pages = utils.pdf_to_images(input_file_path, dpi = 300)
    logger.info(f"Quantidade de imagens geradas a partir do PDF: {len(all_image_pages)}.")

    logger.info("Resultado da análise de documento completo para cada imagem gerada:")
    for image in all_image_pages:
        # 2. Analisar se o documento está completo nas imagens
        doc_completo_resultado = analisar_documento_morfologia(image)
        veredito = doc_completo_resultado.get("status", {})
        motivos = doc_completo_resultado.get("motivos", {})
        if len(motivos) > 1:
            logger.info (f"{str(veredito)} pelos motivos: {str(motivos)}.")
        else:
            logger.info (f"{str(veredito)}.")


    all_results = []
    final_result = []

    for image in all_image_pages:

        if tipo_entrada == "documento_escaneado":
        # 3. Extração de dados com PadddleOCR
            logger.info("Extraindo dados via PaddleOCR.")
            result = processar_documento(image, ocr, MIN_SCORE)

            tipo_doc = result.get("tipo_documento", {})
            logger.info(f"  Tipo identificado: {tipo_doc.get('tipo')}.")

            extracao = result.get("extracao", {})
            campos = extracao.get("campos", {})
            confianca = extracao.get("confianca", {})

            print("\nCAMPOS_EXTRAIDOS\n")
        
            for campo, valor in campos.items():
                confianca_campo = confianca.get(campo, "-")
                print(f"  {campo}: {valor} [{confianca_campo}]\n")

            all_results.append(result)

        elif tipo_entrada == "cnh_digital":
        # 3. Extração de dados com Pytesseract    
            logger.info("Extraindo dados via Pytesseract.")
            resultado_cnh_digital = extract_ecnh(image, lang ="por+eng")

            tipo_doc = resultado_cnh_digital.get("tipo_documento", {})
            logger.info(f"  Tipo identificado: {tipo_doc.get('tipo')}.")

            extracao = resultado_cnh_digital.get("extracao", {})
            campos = extracao.get("campos", {})
            confianca = extracao.get("confianca", {})

            print("\nCAMPOS_EXTRAIDOS\n")

            for campo, valor in campos.items():
                confianca_campo = confianca.get(campo, "-")
                print(f"  {campo}: {valor} [{confianca_campo}]\n")

            all_results.append(resultado_cnh_digital)

        else:
            raise ValueError(
                "tipo_entrada inválido. Use 'documento_escaneado' ou 'cnh_digital'."
            )

    # Escolhe o melhor resultado final entre as páginas
    if len(all_results) > 1:
        final_result = utils.gather_results(all_results)
    else:
        final_result = all_results[0]

    logger.info("RESULTADO FINAL - DADOS OCULTOS")
    extracao_final = final_result.get("extracao", {})
    confianca_final = extracao.get("confianca", {})
    for campo, valor in final_result["extracao"]["campos"].items():
        confianca_campo = confianca_final.get(campo, "-")
        if valor == None:
            logger.info(f"  {campo}: NÃO IDENTIFICADO [{confianca_campo}].")
        else:
            logger.info(f"  {campo}: PREENCHIDO [{confianca_campo}].")
    

    # XML compose
    final_result_with_xml = gerar_xml(final_result, caminho_pdf=input_file_path)
    logger.info(f"Arquivo XML com informações completas gerado.")

    return final_result_with_xml
