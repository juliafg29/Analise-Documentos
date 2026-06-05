import app.services.utils as utils
from app.services.extract_digitalized_data import processar_documento
from app.services.extract_digital_cnh_data import extract_ecnh
from app.services.xml_utils import gerar_xml


def document_workflow(input_file_path, tipo_entrada, ocr, MIN_SCORE = 0.5):

    # Pdf to Image
    all_image_pages = utils.pdf_to_images(input_file_path, dpi = 300)

    all_results = []
    final_result = []

    for image in all_image_pages:

        if tipo_entrada == "documento_escaneado":
        # 2. Extract data with  PadddleOCR
            print("[debug] chegou aqui para processar doc")
            result = processar_documento(image, ocr, MIN_SCORE)

            tipo_doc = result.get("tipo_documento", {})
            print(f"  Tipo: {tipo_doc.get('tipo')}\n")

            extracao = result.get("extracao", {})
            campos = extracao.get("campos", {})
            confianca = extracao.get("confianca", {})

            print("\nCAMPOS_EXTRAIDOS\n")
        
            for campo, valor in campos.items():
                confianca_campo = confianca.get(campo, "-")
                print(f"  {campo}: {valor} [{confianca_campo}]\n")

            all_results.append(result)

        elif tipo_entrada == "cnh_digital":
        
            resultado_cnh_digital = extract_ecnh(image, lang ="por+eng")

            tipo_doc = resultado_cnh_digital.get("tipo_documento", {})
            print(f"  Tipo: {tipo_doc.get('tipo')}\n")

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

    print("\nRESULTADO FINAL\n")
    extracao_final = final_result.get("extracao", {})
    #campos = extracao.get("campos", {})
    confianca_final = extracao.get("confianca", {})
    for campo, valor in final_result["extracao"]["campos"].items():
        confianca_campo = confianca_final.get(campo, "-")
        print(f"  {campo}: {valor} [{confianca_campo}]\n")

    #STEPS FOR DIGITAL CARTEIRA NACIONAL DE HABILITAÇÃO ONLY

    #dados, texto_ocr = extract_ecnh(input_path,lang ="por+eng")

    # XML compose
    final_result_with_xml = gerar_xml(final_result, caminho_pdf=input_file_path)

    return final_result_with_xml
