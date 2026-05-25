# validades PDF

#def validades_PDF(file_path):

#    file = Path(file_path)
#    if not file.filename.lower().endswith(".pdf"):
#        raise HTTPException(status_code=400, detail="Somente PDF é permitido.")
#
#    conteudo_inicial = await file.read(5)
#    if conteudo_inicial != b"%PDF-":
#        raise HTTPException(status_code=400, detail="Arquivo PDF inválido.")
#
#    await file.seek(0)
#
#    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
#
#    conteudo = await file.read()
#    if len(conteudo) > MAX_FILE_SIZE:
#        raise HTTPException(status_code=413, detail="Arquivo muito grande.")
#    
#
#def clean_files:
#    
#    if caminho_temporario and os.path.exists(caminho_temporario):
#        os.remove(caminho_temporario)