"""
Utilitário: converte Artigo_a3.md em Artigo_a3.pdf (entregável da proposta).

Uso:
    python gerar_pdf.py

Requisitos (apenas para gerar o PDF, não fazem parte do deploy):
    pip install markdown
    wkhtmltopdf instalado no sistema (https://wkhtmltopdf.org)
"""

import subprocess

import markdown

ESTILO = """
<meta charset="utf-8">
<style>
  body  { font-family: "Segoe UI", Arial, sans-serif; font-size: 11pt;
          color: #222; line-height: 1.5; margin: 2.2cm; }
  h1    { color: #1b4332; font-size: 17pt; border-bottom: 2px solid #2d6a4f;
          padding-bottom: 6px; }
  h2    { color: #1b4332; font-size: 14pt; margin-top: 24px; }
  h3    { color: #2d6a4f; font-size: 12pt; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; }
  th, td { border: 1px solid #bbb; padding: 6px 10px; font-size: 10pt;
           text-align: left; }
  th    { background: #d8f3dc; color: #1b4332; }
  code  { background: #eef3ef; padding: 1px 5px; border-radius: 3px;
          font-size: 9.5pt; }
  pre   { background: #eef3ef; padding: 10px; border-radius: 6px;
          font-size: 9.5pt; }
  blockquote { border-left: 4px solid #2d6a4f; margin-left: 0;
               padding-left: 14px; color: #555; }
  img   { max-width: 100%; }
</style>
"""


def main():
    with open("Artigo_a3.md", encoding="utf-8") as arquivo:
        html_corpo = markdown.markdown(arquivo.read(),
                                       extensions=["tables", "fenced_code"])

    with open("Artigo_a3.html", "w", encoding="utf-8") as arquivo:
        arquivo.write(ESTILO + html_corpo)

    subprocess.run(["wkhtmltopdf", "--enable-local-file-access",
                    "Artigo_a3.html", "Artigo_a3.pdf"], check=True)
    print("Gerado: Artigo_a3.pdf")


if __name__ == "__main__":
    main()
