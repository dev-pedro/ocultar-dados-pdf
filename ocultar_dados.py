import fitz  # PyMuPDF
import re
import os
import argparse

def ocultar_fatura(input_pdf, output_pdf, texto_ignorar=""):
    try:
        doc = fitz.open(input_pdf)
    except Exception as e:
        print(f"Erro ao abrir {input_pdf}: {e}")
        return

    # Regex para dados sensíveis
    # Valores monetários (ex: R$ 87,20, 1.000,00, etc)
    # CPF (ex: 123.456.789-00)
    regex_sensivel = [
        re.compile(r'R\$\s*[\d\.,]+'), 
        re.compile(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b'), # valor sem R$
        re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b') # CPF
    ]

    for page in doc:
        # Extrair e agrupar palavras por linha (baseado na coordenada vertical (y))
        words = page.get_text("words")
        if not words:
            continue
            
        # Ordenar palavras por y0
        words.sort(key=lambda w: w[1])
        
        lines = []
        for w in words:
            rect = fitz.Rect(w[:4])
            y_center = (rect.y0 + rect.y1) / 2
            
            found_line = False
            for line in lines:
                # Se o centro y da palavra estiver na faixa y da linha (com uma margem de tolerancia)
                if line['y0'] - 3 <= y_center <= line['y1'] + 3:
                    line['words'].append(w)
                    line['y0'] = min(line['y0'], rect.y0)
                    line['y1'] = max(line['y1'], rect.y1)
                    found_line = True
                    break
            
            if not found_line:
                lines.append({'words': [w], 'y0': rect.y0, 'y1': rect.y1})
        
        # Processar cada linha
        for line in lines:
            # Ordenar palavras da linha da esquerda para a direita
            line['words'].sort(key=lambda w: w[0])
            linha_texto = " ".join([w[4] for w in line['words']])
            
            ignorar_esta_linha = False
            if texto_ignorar:
                # Vamos verificar se palavras chaves da entrada do usuario estao na linha
                user_words = [w.lower() for w in texto_ignorar.split() if w.lower() not in ['r$', '-', '–', 'as', 'de', 'do', 'da', 'e']]
                if user_words:
                    matches = 0
                    linha_lower = linha_texto.lower()
                    for w in user_words:
                        if w in linha_lower:
                            matches += 1
                    
                    # Se tivermos pelo menos 70% de match das palavras, consideramos que eh a linha ignorada
                    if matches / len(user_words) >= 0.70:
                        ignorar_esta_linha = True

            if not ignorar_esta_linha:
                tem_sensivel = False
                for regex in regex_sensivel:
                    if regex.search(linha_texto):
                        tem_sensivel = True
                        break
                
                # Se a linha contem dado sensível, ocultamos TODA A LINHA baseada na bounding box completa dela
                if tem_sensivel:
                    x0 = min(w[0] for w in line['words'])
                    y0 = min(w[1] for w in line['words'])
                    x1 = max(w[2] for w in line['words'])
                    y1 = max(w[3] for w in line['words'])
                    
                    # Cria um retangulo com uma pequena margem pra ficar visualmente melhor
                    linha_rect = fitz.Rect(x0 - 2, y0 - 1, x1 + 2, y1 + 1)
                    page.add_redact_annot(linha_rect, fill=(0, 0, 0))

        # Aplica redacoes da pagina
        page.apply_redactions()
    
    doc.save(output_pdf, garbage=4, deflate=True)
    doc.close()
    print(f"Salvo com sucesso: {output_pdf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ocultar faturas em PDF ocultando a linha inteira de dados sensiveis.")
    parser.add_argument("--texto_ignorar", type=str, default="", help="Texto de uma linha para ignorar na ocultacao (ex: '24 FEV Alura')")    
    args = parser.parse_args()

    dir_entrada = "pdf"
    dir_saida = "pdf_oculto"

    if not os.path.exists(dir_saida):
        os.makedirs(dir_saida)

    if not os.path.exists(dir_entrada):
        os.makedirs(dir_entrada)
        print(f"Pasta '{dir_entrada}' criada. Por favor coloque os PDFs na pasta '{dir_entrada}'.")

    arquivos = [f for f in os.listdir(dir_entrada) if f.lower().endswith('.pdf')]
    if not arquivos:
        print(f"Nenhum arquivo PDF encontrado na pasta '{dir_entrada}'.")
    else:
        for f in arquivos:
            caminho_in = os.path.join(dir_entrada, f)
            caminho_out = os.path.join(dir_saida, f"oculto_{f}")
            print(f"Processando '{f}' com texto ignorado: '{args.texto_ignorar}'" if args.texto_ignorar else f"Processando '{f}'...")
            ocultar_fatura(caminho_in, caminho_out, args.texto_ignorar)
