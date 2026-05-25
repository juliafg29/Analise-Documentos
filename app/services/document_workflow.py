from app.services.extract_digital_cnh_data import validar_documento
from app.services.extract_digitalized_data import extrair_dados
from app.services.utils import gerar_xml


def processar_documento(caminho_pdf: str) -> dict:
    """
    Orquestra o fluxo principal de processamento do documento:
    1. valida o PDF;
    2. extrai os dados;
    3. gera a estrutura XML;
    4. retorna o resultado consolidado.
    """

    validacao = validar_documento(caminho_pdf)

    if not validacao["valido"]:
        return {
            "status": "erro",
            "documento_valido": False,
            "mensagens": validacao["mensagens"],
            "dados_extraidos": None,
            "xml": None
        }

    #dados_extraidos = extrair_dados(caminho_pdf)
    dados_extraidos = "Olá"
    #xml_gerado = gerar_xml(dados_extraidos)
    xml_gerado = " Mundo"
    return {
        "status": "sucesso",
        "documento_valido": True,
        "mensagens": validacao["mensagens"],
        "dados_extraidos": dados_extraidos,
        "xml": xml_gerado
    }