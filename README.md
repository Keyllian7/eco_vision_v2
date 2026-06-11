# Eco Vision V2 — Estimativa de Cobertura Vegetal

Projeto da Avaliação A3 da disciplina de **Computação Gráfica** (Ciência da Computação).

## O problema ambiental

**Quantos % de uma área ainda têm vegetação?** O monitoramento de desmatamento
e de arborização urbana depende de quantificar a cobertura vegetal ao longo do
tempo. O Eco Vision V2 responde essa pergunta a partir de uma única imagem
(fotografia ou satélite): aplica um pipeline completo de processamento digital —
pré-processamento, análise de histograma, filtros de suavização, detecção de
bordas e segmentação da vegetação via índice **ExG** (NDVI adaptado para RGB)
com limiarização de **Otsu** e refino morfológico — e entrega o **percentual de
cobertura vegetal** da cena como resultado final.

## Requisitos

- Python 3.10 ou superior
- Bibliotecas: OpenCV (headless), NumPy, Matplotlib, Flask

## Instalação

```bash
# criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# instalar as dependências
pip install -r requirements.txt
```

## Como executar

```bash
python app.py
```

Abra **http://localhost:5000** no navegador, envie a imagem ambiental e
avance pelo pipeline etapa por etapa com o botão **Continuar** — cada card
mostra no máximo duas imagens grandes lado a lado, os dados numéricos e a
explicação da técnica aplicada. O upload já salva o entregável
`imagem_original.png` na pasta do projeto.

## Estrutura do projeto

```
eco_vision_v2/
├── app.py                      # Servidor Flask: rotas e orquestração das etapas
├── processamento/              # Pipeline — um módulo por responsabilidade
│   ├── aquisicao.py            # Leitura/decodificação e conversão BGR → RGB
│   ├── pre_processamento.py    # Escala de cinza, resize e normalização
│   ├── histograma.py           # Análise dos canais R, G e B
│   ├── filtros.py              # Gaussiano, Mediana e Bilateral
│   ├── bordas.py               # Operador Canny
│   ├── segmentacao.py          # ExG + Otsu + morfologia + contornos
│   ├── metricas.py             # PSNR, SNR e cobertura vegetal
│   └── visualizacao.py         # Grids comparativos do relatório
├── templates/index.html        # Página do painel
├── static/                     # Estilo e lógica do frontend
└── resultados/                 # Imagens geradas (grids + imagens do painel)
```

## Saídas geradas

Todas as imagens são salvas na pasta `resultados/`:

| Arquivo | Conteúdo |
|---|---|
| `00_original_vs_cinza.png` | Comparação original × escala de cinza |
| `01_histograma_rgb.png` | Histogramas dos canais R, G e B |
| `02_filtros_comparativo.png` | Grid: original, Gaussiano, Mediana e Bilateral |
| `03_bordas_canny.png` | Bordas detectadas pelo operador Canny |
| `04_segmentacao_otsu.png` | Índice ExG, máscara Otsu, refino morfológico e contornos |
| `05_resumo_pipeline.png` | Resumo visual de todas as etapas |

As métricas (PSNR, SNR, **percentual de cobertura vegetal** e valor médio de
pixel) são exibidas no terminal ao final da execução.

## Etapas do pipeline

1. **Aquisição** — leitura com `cv2.imread()` e conversão BGR → RGB, exibição de metadados
2. **Pré-processamento** — escala de cinza, redimensionamento (largura 800 px) e normalização [0, 1]
3. **Histograma** — distribuição de intensidades dos canais R, G e B
4. **Filtragem** — Gaussiano (σ=1,5), Mediana (kernel 5×5) e Bilateral
5. **Detecção de bordas** — Canny com limiares 50 e 150 (histerese)
6. **Segmentação da vegetação** — índice ExG (2G−R−B, NDVI adaptado para RGB) +
   limiarização de Otsu + abertura e fechamento morfológicos
7. **Métricas** — PSNR, SNR, cobertura vegetal (%) e valor médio de pixel
8. **Visualização** — grids comparativos gerados com Matplotlib
