# GeoAquaCrop — WebGIS

WebGIS local para rodar o **GeoAquaCrop** (AquaCrop-OSPy em grade) sobre uma área
desenhada no mapa ou enviada como arquivo, e explorar os resultados em mapas e gráficos.
Interface em **português e inglês** (seletor PT/EN no topo do painel esquerdo).
*English version: [README.en.md](README.en.md).*

Esta é a interface web do GeoAquaCrop, desenvolvido por **Christopher (Chris) Bowden**
(University of Manchester), Josias Láng-Ritter, Seyed Hossein Hosseini (Aalto University),
E. Alkio, Henrikki Tenkanen (Aalto University) e Timothy (Tim) Foster (University of Manchester).
Veja [Créditos](#créditos).

```
navegador (Leaflet + Chart.js)          servidor local (FastAPI, Python)
┌─────────────┬──────────┬──────────┐    ┌──────────────────────────────────────────┐
│ passos e    │  mapa    │ resultados│◀──▶│ área → geoaquacrop_preprocess (por etapa) │
│ orientações │ (desenho,│ KPIs,     │    │      → geoaquacrop_simulate (por célula)  │
│ período,    │  busca,  │ gráficos, │    │      → resultados (CSV, NetCDF, GeoJSON)  │
│ execução    │  grade)  │ modal     │    │ fila, progresso, cache e temporários      │
└─────────────┴──────────┴──────────┘    └──────────────────────────────────────────┘
```

## Instalar (Windows)

Precisa de Python 3.11, 3.12 ou 3.13.

**Opção A — venv (mais simples):** dê duplo clique em `instalar_geocrop.bat`.

**Opção B — conda (recomendada se a opção A falhar em rasterio/GDAL):**

```bat
conda env create -f environment.yml
conda activate geocrop
```

## Rodar

Duplo clique em `iniciar_geocrop.bat` (ou `python run.py`). O navegador abre em
<http://127.0.0.1:8050>. O servidor só escuta na própria máquina.

Para teste rápido sem baixar nada, escolha **Demonstração** no passo 4.

## Fluxo na interface

1. **Área de interesse** — desenhe polígono ou retângulo, envie GeoJSON, KML, KMZ,
   GeoPackage ou shapefile em .zip (arrastar para o mapa também funciona), ou busque
   um município/estado/bacia e use o limite como área. Tudo vira um único polígono
   em EPSG:4326; arquivos em outro sistema são reprojetados, geometrias inválidas são
   corrigidas e o painel avisa quando a área é pequena demais para o clima (< 0,25°).
2. **Cultura e manejo** — 15 culturas do toolchain; sequeiro ou irrigado.
3. **Período, clima e grade** — anos inicial e final. A fonte de clima segue a regra
   do GeoAquaCrop: AgERA5 (1979 até o ano anterior, exige token do Copernicus CDS)
   ou NASA NEX-GDDP-CMIP6 (períodos que chegam ao ano atual/futuro; modelo e SSP
   escolhidos aqui). Resolução da grade com estimativa de células e de tempo.
4. **Executar** — progresso por etapa, registro detalhado e cancelamento.

O painel direito mostra o mapa da variável escolhida (por safra ou média), KPIs,
produtividade por safra, balanço hídrico, distribuição entre células e, ao clicar numa
célula, as séries diárias (dossel, biomassa, chuva × ET, água na zona radicular).
Cada gráfico abre em modal com tabela e CSV. **Baixar** entrega:

| Arquivo | Conteúdo |
|---|---|
| `seasons.csv` | Uma linha por célula e safra: produtividades, chuva, ET, Tr, Es, escoamento, percolação, irrigação, WP |
| `yield_grid.nc` | Grade (ano, y, x) das variáveis principais, para SIG |
| `cells.geojson` | Células como polígonos com atributos por ano (abre direto no QGIS) |
| `daily.nc` | Séries diárias de todas as células (int16 compactado) |
| `aoi.geojson` | O polígono exato usado |
| `model/summary_results_*.pkl` | Formato do próprio toolchain (`gac.simulate.load_results`, visualize) |

## Downloads, cache e temporários

* Tudo o que é baixado vai para `data/tmp/<análise>` e essa pasta **é apagada ao fim
  de cada análise**, com sucesso, erro ou cancelamento.
* Ficam guardados de propósito:
  - `data/cache/global` — arquivos globais do SPAM e do GGCMI, iguais para qualquer
    área (centenas de MB; baixá-los toda vez é o que deixaria o sistema lento);
  - `data/cache/areas/<área>` — os recortes **processados** de cada área (pequenos),
    para que trocar só a cultura, o regime ou as opções rode sem novo download.
    Desligável por análise ("Reaproveitar os dados desta área").
* O botão **Cache** (abaixo do histórico) mostra o tamanho e limpa cada parte.

## Opções científicas (passo 3 → Opções avançadas)

Desligadas por padrão, para reproduzir o toolchain original:

* **Perfil de solo de 2 m** — o toolchain cria o solo com os 12 compartimentos de 0,1 m
  do AquaCrop-OSPy (1,2 m), o que desloca as camadas do SoilGrids e descarta a de
  100–200 cm. A opção usa compartimentos alinhados às seis camadas (2,0 m).
* **CO₂ do cenário SSP** — sem ela, o AquaCrop usa a série Mauna Loa + A1B para
  qualquer cenário. Só altera projeções.

Independentemente das opções, a interface recalcula **por safra** chuva, ET, Tr, Es,
escoamento, percolação e produtividade da água a partir da saída diária (do plantio à
maturação). As colunas `seasonal_et_mm` e `seasonal_precip_mm` do toolchain somam o
período inteiro e repetem o total em todas as safras, o que distorce a WP.

## Configuração (opcional)

Copie `config.example.json` para `config.json`:

| Chave | Uso |
|---|---|
| `cds_api_token` | Token do Copernicus CDS, para não digitar a cada análise |
| `google_maps_api_key` | Ativa o satélite do Google pela API oficial (Maps JavaScript API). Sem chave, usa Esri. Usar os tiles do Google sem a API viola os termos de uso |
| `workers` | Processos de simulação (0 = núcleos − 1) |
| `max_cells` | Limite de células por análise real (padrão 20 000) |
| `nominatim_contact` | E-mail enviado à busca do OpenStreetMap, como pede a política de uso |

Também valem variáveis de ambiente `GEOCROP_<CHAVE>` (ex.: `GEOCROP_CDS_API_TOKEN`).

## Limitações conhecidas

* **Tempo**: AgERA5 depende da fila do Copernicus CDS (de minutos a horas). A primeira
  análise baixa o SPAM e o GGCMI globais; as seguintes reaproveitam.
* **Cancelar** para entre etapas e entre células; um download em curso do pré-processamento
  termina antes. O `download_url` do toolchain tenta de novo indefinidamente quando a
  rede cai, então uma queda longa de internet mantém a etapa parada.
* Safras que não terminam até 31/12 do último ano não são simuladas; o ano da safra é o
  da colheita (no Hemisfério Sul a primeira colheita costuma cair no ano seguinte ao início).
* A demonstração usa dados **inventados** para clima, solo, calendário e área: serve para
  testar o fluxo, não para interpretar a região.
* Mapas de fundo e busca precisam de internet; o resto (bibliotecas, fontes) vem em
  `frontend/vendor` e funciona offline.

## Estrutura

```
GeoCrop/                      (pasta do projeto; o pacote Python interno chama-se geocrop)
├── run.py                    inicia o servidor
├── backend/geocrop/
│   ├── app.py                API e arquivos estáticos
│   ├── i18n.py               mensagens do servidor em PT e EN
│   ├── aoi.py                GeoJSON/KML/KMZ/SHP → polígono EPSG:4326
│   ├── search.py             busca de lugares (Nominatim)
│   ├── jobs.py               fila e estado das análises
│   ├── pipeline.py           área → pré-processamento (com cache) → simulação → limpeza
│   ├── sim_worker.py         wrapper do worker por célula do geoaquacrop_simulate
│   ├── daily_store.py        séries diárias em NetCDF compacto
│   ├── results.py            estatísticas, mapa, CSV, NetCDF, GeoJSON
│   └── synthetic.py          entradas sintéticas da demonstração
├── frontend/                 HTML, CSS, JS (Leaflet, Leaflet.draw, Chart.js locais)
│   └── js/i18n.js            textos da interface em PT e EN
├── tests/                    python -m pytest -q
└── data/                     criado na primeira execução (análises, cache, temporários)
```

## Créditos

O pré-processamento e a simulação vêm dos pacotes do **GeoAquaCrop**, desenvolvidos por:

| Autor | Instituição |
|---|---|
| **Christopher (Chris) Bowden** — mantenedor do `geoaquacrop_simulate` | University of Manchester |
| Josias Láng-Ritter | Aalto University |
| Seyed Hossein Hosseini | Aalto University |
| E. Alkio | |
| Henrikki Tenkanen | Aalto University |
| Timothy (Tim) Foster | University of Manchester |

**Como citar.** Ao publicar resultados, cite o GeoAquaCrop e o AquaCrop-OSPy. Enquanto o
preprint não sai, os autores pedem:

> Láng-Ritter, J., Bowden, C., Hosseini, S., Alkio, E., Tenkanen, H. & Foster, T. GeoAquaCrop:
> Large-scale agricultural crop modelling using open global data (preprint em preparação).
>
> Kelly, T. D. & Foster, T. (2021). AquaCrop-OSPy: Bridging the gap between research and
> practice in crop-water modelling. *Agricultural Water Management* 254, 106976.
> doi:10.1016/j.agwat.2021.106976

**Modelo:** AquaCrop (FAO; Steduto, Hsiao, Raes & Fereres, 2009), AquaCrop-OS (Foster et al., 2017),
AquaCrop-OSPy (Kelly & Foster, 2021).

**Dados:** AgERA5 (Copernicus C3S, Boogaard et al. 2020), NASA NEX-GDDP-CMIP6 (Thrasher et al. 2022),
SoilGrids 2.0 (ISRIC, Poggio et al. 2021), GGCMI fase 3 (Jägermeyr et al. 2021), MARC (Zhao et al. 2024),
SPAM (IFPRI, Yu et al. 2020). Cite também as fontes de dados usadas.

**Mapa e software:** Esri, OpenStreetMap, CARTO, OpenStreetMap Nominatim; Leaflet, Leaflet.draw,
Chart.js, FastAPI, fonte Public Sans. GeoAquaCrop e AquaCrop-OSPy usam a licença Apache-2.0.

Os mesmos créditos aparecem na interface (link **Créditos** no rodapé do painel esquerdo).
