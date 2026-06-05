import os
from pdf2image import convert_from_path
from PIL import Image
from PIL.Image import DecompressionBombError
import cv2
import numpy as np

import logging
from paddleocr import PaddleOCR


def pdf_to_images(caminho_pdf: str, dpi: int = 300) -> list[np.ndarray]:
    """
    Converte cada página de um PDF em uma imagem no formato np.ndarray.

    Retorna:
        todas_paginas: lista de imagens, onde cada imagem é um np.ndarray
                       no formato BGR, compatível com OpenCV.
    """

    paginas = convert_from_path(caminho_pdf, dpi=dpi)

    todas_paginas: list[np.ndarray] = []

    for pagina in paginas:
        # pagina vem como PIL.Image
        imagem_np = np.array(pagina)

        # Converte RGB para BGR, padrão usado pelo OpenCV
        imagem_cv = cv2.cvtColor(imagem_np, cv2.COLOR_RGB2BGR)

        todas_paginas.append(imagem_cv)
    print(type(todas_paginas))
    print(type(todas_paginas[0]))
    return todas_paginas

def compose_paddle_ocr():
    logging.getLogger('ppocr').setLevel(logging.WARNING)

    ocr_paddleocr = PaddleOCR(use_angle_cls=True, lang='pt')

    return ocr_paddleocr

def gather_results(results:list):

    if not results:
        return None

    # Começa usando o primeiro resultado como base
    resultado_final = results[0].copy()

    extracao_final = resultado_final.get("extracao", {})
    campos_finais = extracao_final.get("campos", {})
    confianca_final = extracao_final.get("confianca", {})

    for resultado in results[1:]:

        extracao = resultado.get("extracao", {})
        campos = extracao.get("campos", {})
        confianca = extracao.get("confianca", {})

        for campo, valor in campos.items():

            valor_atual = campos_finais.get(campo)

            # Verifica se o valor atual está vazio
            vazio = (
                valor_atual is None
                or valor_atual == ""
                or str(valor_atual).strip().lower() == "none"
            )

            # Se estiver vazio e o novo valor existir, substitui
            if vazio and valor not in [None, "", "None"]:

                campos_finais[campo] = valor

                if campo in confianca:
                    confianca_final[campo] = confianca[campo]

    # Atualiza estrutura final
    resultado_final["extracao"]["campos"] = campos_finais
    resultado_final["extracao"]["confianca"] = confianca_final

    return resultado_final