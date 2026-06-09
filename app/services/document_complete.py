import os
import cv2
import numpy as np
from datetime import datetime

# Passa imagem para escala de cinza
def _to_gray(imagem):
    if imagem is None:
        raise ValueError("Imagem inválida.")
    if len(imagem.shape) == 3:
        return cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    return imagem.copy()

# Gera uma máscara binária utilizando 2 métodos diferentes. Destaca as regiões de interesse na imagem
def _binarizar_documento(gray):
    """
    Testa Otsu e adaptativo, e escolhe a máscara mais plausível.
    """
    # Aplica suavização com filtro Gaussiano
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Limiarização global pelo método de Otsu
        # O Otsu escolhe automaticamente um limiar que separa pixels
        # claros e escuros com base no histograma da imagem.
    _, otsu = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Limiarização adaptativa. Ideal para imagens com iluminação irregular
        # Diferente do Otsu, que usa um único limiar global,
        # o método adaptativo calcula limiares locais.
        # Isso ajuda em imagens com iluminação irregular.
    adap = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 15
    )

    # Normaliza a imagem binária para que o conteúdo de interesse fique branco e o fundo fique preto.
    def normalizar(binaria):
        if np.mean(binaria) > 127:
            binaria = 255 - binaria
        return binaria

    otsu = normalizar(otsu)
    adap = normalizar(adap)

    # Calcula a fração de pixels brancos em cada máscara. A fração indica quanto da imagem foi considerado conteúdo
    frac_otsu = np.mean(otsu == 255)
    frac_adap = np.mean(adap == 255)

    alvo = 0.25

    # Calcula o quanto cada método se aproxima da fração-alvo
    score_otsu = abs(frac_otsu - alvo)
    score_adap = abs(frac_adap - alvo)

    # Escolhe a máscara cuja proporção de pixels brancos está mais próxima do valor esperado
    escolhida = otsu if score_otsu < score_adap else adap
    return blur, otsu, adap, escolhida

# Operações morfológicas para melhorar a máscara binária: conectar partes e remover ruídos
def _fechar_e_limpar(binaria, kernel_close=(15, 15), kernel_open=(5, 5), it_close=2, it_open=1):

    # Uni regiões próximas
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_close)
    # Destroi ruídos
    k_open = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_open)

    # Preenche falhas e conecta componentes
    fechado = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, k_close, iterations=it_close)
    limpo = cv2.morphologyEx(fechado, cv2.MORPH_OPEN, k_open, iterations=it_open)

    return fechado, limpo

# Escolha dos componentes relevantes para análise
def _pontuar_componente(x, y, w, h, area, altura_img, largura_img):

    # Área do retângulo delimitador do componente
    area_bbox = w * h
    if area_bbox == 0:
        return -1e9, {}

    area_img = altura_img * largura_img
    # Fração da área total da imagem ocupada pelo componente
    frac_area = area / area_img
    retangularidade = area / area_bbox
    aspect_ratio = w / h if h > 0 else 0

    cx = x + w / 2
    cy = y + h / 2
    dist_centro = np.sqrt((cx - largura_img / 2) ** 2 + (cy - altura_img / 2) ** 2)

    # Normalização da distância pelo maior deslocamento possível
    dist_centro_norm = dist_centro / np.sqrt((largura_img / 2) ** 2 + (altura_img / 2) ** 2)

    # Pontuação baseada na área.
    # Componentes muito pequenos tendem a ser ruído, assinatura ou QR code.
    # Componentes muito grandes podem representar fundo ou segmentação ruim.
    if 0.08 <= frac_area <= 0.95:
        score_area = 3.0
    elif 0.03 <= frac_area < 0.08:
        score_area = 1.5
    else:
        score_area = -2.0

    # Pontuação baseada na retangularidade.
    score_ret = 4.0 * retangularidade

    # Pontuação baseada na proporção geométrica.
    if 0.45 <= aspect_ratio <= 2.2:
        score_aspect = 2.5
    else:
        score_aspect = -2.0

    score_centro = 1.5 * (1 - dist_centro_norm)

    score_total = score_area + score_ret + score_aspect + score_centro

    # Informações para registro em log
    info = {
        "frac_area": frac_area,
        "retangularidade": retangularidade,
        "aspect_ratio": aspect_ratio,
        "dist_centro_norm": dist_centro_norm,
        "score_total": score_total
    }
    return score_total, info

# Função principal: Detecta o documento principal e avalia se está completo.
def analisar_documento_morfologia(
    imagem,
    area_min_frac=0.02,
    margem=8,
    kernel_close=(15, 15),
    kernel_open=(5, 5),
    it_close=2,
    it_open=1
):

    original = imagem.copy()

    # Obtém dimensões da imagem
    altura, largura = original.shape[:2]
    area_total = altura * largura
    area_min = int(area_total * area_min_frac)

    # Etapa 1: conversão para escala de cinza
    gray = _to_gray(original)

    # Etapa 2: suavização e binarização
    blur, otsu, adap, binaria = _binarizar_documento(gray)

    # Etapa 3: fechamento e abertura morfológica
    fechado, limpo = _fechar_e_limpar(
        binaria,
        kernel_close=kernel_close,
        kernel_open=kernel_open,
        it_close=it_close,
        it_open=it_open
    )

    # Etapa 4: identificação de componentes conectados
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(limpo, connectivity=8)

    candidatos = []

    # Percorre todos os componentes detectados
    for label in range(1, num_labels):

        # Extrai posição, dimensões e área do componente
        x = stats[label, cv2.CC_STAT_LEFT]
        y = stats[label, cv2.CC_STAT_TOP]
        w = stats[label, cv2.CC_STAT_WIDTH]
        h = stats[label, cv2.CC_STAT_HEIGHT]
        area = stats[label, cv2.CC_STAT_AREA]

        # Ignora componentes pequenos demais
        if area < area_min:
            continue

        # Calcula pontuação geométrica do componente
        score, info = _pontuar_componente(x, y, w, h, area, altura, largura)
        # Armazena o componente como candidato a documento principal
        candidatos.append({
            "label": label,
            "x": x, "y": y, "w": w, "h": h,
            "area": area,
            "score": score,
            **info
        })

    resultado = original.copy()
    mascara_doc = np.zeros((altura, largura), dtype=np.uint8)

    # Caso 1: nenhum componente relevante encontrado
    if not candidatos:
        texto = "Documento nao detectado"
        cv2.putText(
            resultado, texto, (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2, cv2.LINE_AA
        )

        return {
            "status": "Não detectado",
            "completo": False,
            "conclusao": "Nenhum documento foi detectado.",
            "motivos": ["Nenhum componente relevante foi encontrado após morfologia."],
            "bbox": None,
            "melhor_candidato": None,
            "candidatos": [],
            "imagens_intermediarias": {
                "gray": gray,
                "blur": blur,
                "otsu": otsu,
                "adaptativo": adap,
                "binaria_escolhida": binaria,
                "fechado": fechado,
                "limpo": limpo,
                "mascara_documento": mascara_doc,
                "resultado": resultado
            }
        }

    # Seleciona o candidato com maior pontuação, que será o principal
    melhor = max(candidatos, key=lambda c: c["score"])
    x, y, w, h = melhor["x"], melhor["y"], melhor["w"], melhor["h"]
    label_doc = melhor["label"]

    # Cria uma máscara contendo apenas o componente escolhido
    mascara_doc[labels == label_doc] = 255

    motivos = []

    # Analise se o documento encosta na borda. Se isso acontece, o documento pode estar cortado.
    # A variável margem define uma tolerância em pixels
    toca_esquerda = x <= margem
    toca_topo = y <= margem
    toca_direita = (x + w) >= (largura - margem)
    toca_inferior = (y + h) >= (altura - margem)

    # Caso 2: documento encosta em alguma borda
    if toca_esquerda:
        motivos.append("O documento encosta na borda esquerda.")
    if toca_topo:
        motivos.append("O documento encosta na borda superior.")
    if toca_direita:
        motivos.append("O documento encosta na borda direita.")
    if toca_inferior:
        motivos.append("O documento encosta na borda inferior.")

    #if melhor["retangularidade"] < 0.25:
    #    motivos.append(
    #        f"O componente detectado tem baixa retangularidade ({melhor['retangularidade']:.2f})."
    #    )

    # Se não houver motivos de incompletude, considera-se completo
    completo = len(motivos) == 0
    status = "Completo" if completo else "Incompleto"

    # Desenha todos os elementos identificados em azul.
    # Esses elementos correspondem aos componentes conectados relevantes
    # encontrados após a etapa de morfologia.
    cor_elemento = (255, 0, 0)  # azul em BGR

    for cand in candidatos:
        cx = cand["x"]
        cy = cand["y"]
        cw = cand["w"]
        ch = cand["h"]

        cv2.rectangle(
            resultado,
            (cx, cy),
            (cx + cw, cy + ch),
            cor_elemento,
            2
        )

    # Desenha o documento principal por cima dos retângulos azuis.
    # Verde = documento completo.
    # Vermelho = documento possivelmente cortado/incompleto.
    cor = (0, 255, 0) if completo else (0, 0, 255)
    cv2.rectangle(resultado, (x, y), (x + w, y + h), cor, 4)

    # Desenha um retangulo colorido na área que identificou o documento
    cor = (0, 255, 0) if completo else (0, 0, 255)
    cv2.rectangle(resultado, (x, y), (x + w, y + h), cor, 3)

    texto = "Documento completo" if completo else "Documento possivelmente cortado"
    cv2.putText(
        resultado, texto, (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, cor, 2, cv2.LINE_AA
    )

    # Texto final da conclusão
    conclusao = (
        "O documento aparenta estar completo na imagem."
        if completo
        else "O documento aparenta estar cortado ou incompleto na imagem."
    )

    # Retorna resultados quantitativos, diagnóstico e imagens intermediárias
    return {
        "status": status,
        "completo": completo,
        "conclusao": conclusao,
        "motivos": motivos,
        "bbox": (x, y, w, h),
        "melhor_candidato": melhor,
        "candidatos": candidatos,
        "imagens_intermediarias": {
            "gray": gray,
            "blur": blur,
            "otsu": otsu,
            "adaptativo": adap,
            "binaria_escolhida": binaria,
            "fechado": fechado,
            "limpo": limpo,
            "mascara_documento": mascara_doc,
            "resultado": resultado
        }
    }
