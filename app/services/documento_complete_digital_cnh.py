# Código alternativo para detectar se o documento está completo
# Apresentou melhores resultados apenas para CNH Digital

import cv2
import numpy as np

def to_gray(image):
    """
    Converte a imagem para tons de cinza.
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image.copy()


def score_contorno_documento(cnt, area_img, w_img, h_img, margin):
    """
    Avalia se um contorno parece ser um documento.

    Métodos clássicos usados:
    - Análise geométrica de contornos
    - Bounding box
    - Aproximação poligonal
    - Retângulo rotacionado mínimo
    """
    area = cv2.contourArea(cnt)
    if area <= 0:
        return None

    x, y, w, h = cv2.boundingRect(cnt)
    bbox_area = w * h
    if bbox_area <= 0:
        return None

    area_frac = area / area_img
    fill_ratio = area / bbox_area
    aspect = w / h if h > 0 else 0

    # Aproximação poligonal do contorno
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.025 * peri, True)

    # Retângulo rotacionado mínimo
    rect = cv2.minAreaRect(cnt)
    rw, rh = rect[1]
    rotated_area = rw * rh if rw > 0 and rh > 0 else 0
    fill_rot = area / rotated_area if rotated_area > 0 else 0

    toca_borda = (
        x <= margin or
        y <= margin or
        x + w >= w_img - margin or
        y + h >= h_img - margin
    )

    # Filtros geométricos
    if area_frac < 0.03:
        return None

    if area_frac > 0.98:
        return None

    if fill_ratio < 0.20:
        return None

    if fill_rot < 0.25:
        return None

    if not (0.20 <= aspect <= 5.00):
        return None

    # Score do candidato
    score = 0.0
    score += 3.0 * area_frac
    score += 2.0 * fill_ratio
    score += 1.5 * fill_rot

    if len(approx) == 4:
        score += 2.0
    elif 4 < len(approx) <= 8:
        score += 1.0
    elif len(approx) <= 10:
        score += 0.4

    if toca_borda:
        score -= 1.0

    return {
        "score": score,
        "bbox": (x, y, w, h),
        "approx": approx,
        "rect": rect,
        "area_frac": area_frac,
        "fill_ratio": fill_ratio,
        "fill_rot": fill_rot,
        "aspect": aspect,
        "toca_borda": toca_borda
    }


def detectar_documento_contorno(orig, mostrar_etapas=False):
    """
    Detecta se há um documento completo na imagem.

    """

    gray = to_gray(orig)
    h, w = gray.shape[:2]
    area_img = h * w

    # Critério de borda mais tolerante
    margin = 10

    # 1) Filtragem com Bilateral Filter
    blur = cv2.bilateralFilter(gray, 9, 50, 50)

    # 2) Realce de contraste com Histogram Equalization
    blur = cv2.equalizeHist(blur)

    # 3) Detecção de bordas com Canny Edge Detector
    edges = cv2.Canny(blur, 40, 140)

    # 4) Pós-processamento com fechamento morfológico + dilatação
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    fechado = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    fechado = cv2.dilate(fechado, kernel_dilate, iterations=1)

    # 5) Extração de contornos com FindContours
    contours, _ = cv2.findContours(fechado, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    imagem_saida = orig.copy()
    if len(imagem_saida.shape) == 2:
        imagem_saida = cv2.cvtColor(imagem_saida, cv2.COLOR_GRAY2BGR)

    motivos = []

    if not contours:
        motivos.append("Nenhum contorno externo relevante foi encontrado.")
        if mostrar_etapas:
            mostrar_pipeline(orig, gray, edges, fechado, imagem_saida, "Documento não identificado")
        return {
            "completo": False,
            "bbox": None,
            "imagem_resultado": imagem_saida,
            "motivos": motivos
        }

    # 6) Escolha do melhor candidato
    melhor = None
    melhor_info = None

    for cnt in contours:
        info = score_contorno_documento(cnt, area_img, w, h, margin)
        if info is None:
            continue

        if melhor is None or info["score"] > melhor_info["score"]:
            melhor = cnt
            melhor_info = info

    if melhor is None:
        motivos.append("Nenhum contorno satisfez os critérios geométricos.")
        if mostrar_etapas:
            mostrar_pipeline(orig, gray, edges, fechado, imagem_saida, "Documento não identificado")
        return {
            "completo": False,
            "bbox": None,
            "imagem_resultado": imagem_saida,
            "motivos": motivos
        }

    # 7) Decisão final
    x, y, bw, bh = melhor_info["bbox"]
    area_frac = melhor_info["area_frac"]
    fill_ratio = melhor_info["fill_ratio"]
    fill_rot = melhor_info["fill_rot"]
    aspect = melhor_info["aspect"]

    completo = True

    if area_frac < 0.06:
        completo = False
        motivos.append(f"Área muito pequena ({area_frac:.2%} da imagem).")

    if fill_ratio < 0.30:
        completo = False
        motivos.append(f"Retangularidade baixa no bounding box ({fill_ratio:.2f}).")

    if fill_rot < 0.35:
        completo = False
        motivos.append(f"Retangularidade baixa no retângulo rotacionado ({fill_rot:.2f}).")

    if not (0.25 <= aspect <= 4.00):
        completo = False
        motivos.append(f"Proporção fora do esperado ({aspect:.2f}).")

    if x <= margin:
        completo = False
        motivos.append("Muito próximo da borda esquerda.")
    if y <= margin:
        completo = False
        motivos.append("Muito próximo da borda superior.")
    if x + bw >= w - margin:
        completo = False
        motivos.append("Muito próximo da borda direita.")
    if y + bh >= h - margin:
        completo = False
        motivos.append("Muito próximo da borda inferior.")

    # 8) Desenho do retângulo rotacionado mínimo
    box = cv2.boxPoints(melhor_info["rect"])
    box = np.intp(box)

    if completo:
        cv2.polylines(imagem_saida, [box], True, (0, 255, 0), 3)
        titulo = "Documento completo identificado"
    else:
        cv2.polylines(imagem_saida, [box], True, (0, 0, 255), 3)
        titulo = "Documento identificado, mas incompleto"

    if mostrar_etapas:
        mostrar_pipeline(orig, gray, edges, fechado, imagem_saida, titulo)

    return {
        "completo": completo,
        "bbox": (x, y, bw, bh),
        "imagem_resultado": imagem_saida,
        "motivos": motivos
    }

