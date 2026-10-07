// Interface language (Portuguese / English).
// Static text in index.html uses data-i18n* attributes; scripts call t().
// Server messages arrive translated through the X-Lang header, and step
// progress comes as a message key so it follows the selected language.

const D = {
  // ------------------------------------------------------------ chrome --
  "brand.sub": ["AquaCrop em grade sobre a sua área", "Gridded AquaCrop over your area"],
  "lang.label": ["Idioma", "Language"],
  "panel.close": ["Fechar painel", "Close panel"],
  "panel.open": ["Abrir configuração", "Open settings"],
  "results.open": ["Abrir resultados", "Open results"],
  "results.collapse": ["Recolher resultados", "Collapse results"],
  "map.aria": ["Mapa", "Map"],
  "search.placeholder": ["Buscar município, estado, bacia, país…", "Search municipality, state, basin, country…"],
  "search.aria": ["Buscar lugar", "Search place"],
  "search.searching": ["Buscando…", "Searching…"],
  "search.none": ["Nada encontrado para “{q}”.", "Nothing found for “{q}”."],
  "search.has_boundary": ["Tem limite (polígono)", "Has a boundary (polygon)"],
  "search.point_only": ["Só localização", "Location only"],
  "search.use": ["Usar como área", "Use as area"],
  "drop.hint": ["Solte o arquivo para usar como área", "Drop the file to use it as the area"],
  "footer.based": ["GeoAquaCrop, de C. Bowden, J. Láng-Ritter, S. H. Hosseini, E. Alkio, H. Tenkanen e T. Foster.",
    "GeoAquaCrop, by C. Bowden, J. Láng-Ritter, S. H. Hosseini, E. Alkio, H. Tenkanen and T. Foster."],
  "footer.credits": ["Créditos", "Credits"],

  // ------------------------------------------------------------- step 1 --
  "s1.title": ["Área de interesse", "Area of interest"],
  "s1.none": ["não definida", "not defined"],
  "s1.guide": ["Desenhe no mapa, envie um arquivo ou busque um município, estado ou bacia. A área vira um polígono em WGS84 (EPSG:4326), que é o que o pré-processamento exige.",
    "Draw on the map, upload a file or search for a municipality, state or basin. The area becomes a WGS84 (EPSG:4326) polygon, which is what the preprocessing requires."],
  "s1.draw_poly": ["Desenhar polígono", "Draw polygon"],
  "s1.draw_rect": ["Desenhar retângulo", "Draw rectangle"],
  "s1.upload": ["Enviar arquivo", "Upload file"],
  "s1.search": ["Buscar região", "Search region"],
  "s1.formats": ["GeoJSON, KML, KMZ, GeoPackage ou shapefile em .zip (com .shp, .shx, .dbf e .prj). Também dá para arrastar o arquivo para o mapa. Outros sistemas de coordenadas são reprojetados.",
    "GeoJSON, KML, KMZ, GeoPackage or a zipped shapefile (.shp, .shx, .dbf and .prj). You can also drag the file onto the map. Other coordinate systems are reprojected."],
  "s1.remove": ["Remover", "Remove"],
  "s1.area": ["Área", "Area"],
  "s1.parts": ["Partes", "Parts"],
  "s1.extent": ["Extensão", "Extent"],
  "s1.unnamed": ["Área sem nome", "Unnamed area"],
  "s1.drawn": ["Área desenhada", "Drawn area"],
  "s1.draw_poly_hint": ["Clique no mapa para marcar os vértices; clique no primeiro para fechar.", "Click on the map to place vertices; click the first one to close."],
  "s1.draw_rect_hint": ["Clique e arraste no mapa.", "Click and drag on the map."],
  "s1.set": ["Área definida: {area} km²", "Area set: {area} km²"],
  "s1.reading": ["Lendo {name}…", "Reading {name}…"],
  "s1.from_file": ["Área de {name}: {area} km²", "Area from {name}: {area} km²"],

  // AOI warnings (server sends keys, so they follow the selected language)
  "aoi.no_crs": ["O arquivo não declara sistema de coordenadas; assumi WGS84 (EPSG:4326). Confira se a área caiu no lugar certo.", "The file declares no coordinate system; WGS84 (EPSG:4326) was assumed. Check that the area landed in the right place."],
  "aoi.reprojected": ["Reprojetado de {crs} para WGS84 (EPSG:4326).", "Reprojected from {crs} to WGS84 (EPSG:4326)."],
  "aoi.dropped": ["{n} geometria(s) que não são polígonos foram ignoradas.", "{n} non-polygon geometry(ies) were ignored."],
  "aoi.fixed": ["Geometria com autointerseção foi corrigida automaticamente.", "A self-intersecting geometry was repaired automatically."],
  "aoi.small": ["Área com menos de 0,25° de lado (~25 km). Os dados de clima têm 0,1–0,25° de resolução: o resultado será pouco detalhado e a etapa de clima pode falhar.", "Area smaller than 0.25° across (~25 km). Climate data have 0.1–0.25° resolution: results will be coarse and the climate step may fail."],
  "aoi.simplified": ["Contorno com {n} vértices simplificado (tolerância ~100 m).", "Outline with {n} vertices simplified (~100 m tolerance)."],

  // ------------------------------------------------------------- step 2 --
  "s2.title": ["Cultura e manejo", "Crop and management"],
  "s2.guide": ["A cultura define os parâmetros padrão do AquaCrop e as camadas do calendário agrícola (GGCMI) e da área plantada (SPAM). O ciclo de cada célula é ajustado à data de plantio e à duração locais.",
    "The crop sets AquaCrop's default parameters and the crop-calendar (GGCMI) and crop-area (SPAM) layers used. Each cell's cycle is adjusted to the local planting date and season length."],
  "s2.crop": ["Cultura", "Crop"],
  "s2.regime": ["Regime hídrico", "Water regime"],
  "irr.rainfed": ["Sequeiro", "Rainfed"],
  "irr.irrigated": ["Irrigado", "Irrigated"],
  "irr.rainfed_lc": ["sequeiro", "rainfed"],
  "irr.irrigated_lc": ["irrigado", "irrigated"],
  "s2.hint_rainfed": ["Sequeiro: só chuva. A produtividade cai quando falta água no solo.", "Rainfed: rain only. Yield drops when soil water runs short."],
  "s2.hint_irrigated": ["Irrigado: o AquaCrop irriga sempre que a umidade cai abaixo de 80% da água disponível, sem limite de lâmina. Representa a produtividade com água garantida.",
    "Irrigated: AquaCrop irrigates whenever soil moisture falls below 80% of available water, with no seasonal cap. It represents yield with guaranteed water."],

  // ------------------------------------------------------------- step 3 --
  "s3.title": ["Período, clima e grade", "Period, climate and grid"],
  "s3.guide": ["Os anos definem o clima a baixar. A fonte segue a regra do GeoAquaCrop: anos passados (1979 até o ano anterior) usam AgERA5; períodos que chegam ao ano atual ou ao futuro usam projeções NASA NEX-GDDP-CMIP6.",
    "The years define which climate is downloaded. The source follows the GeoAquaCrop rule: past years (1979 to last year) use AgERA5; periods reaching the current year or the future use NASA NEX-GDDP-CMIP6 projections."],
  "s3.start": ["Ano inicial", "Start year"],
  "s3.end": ["Ano final", "End year"],
  "s3.token": ["Token da API do Copernicus CDS", "Copernicus CDS API token"],
  "s3.token_ph": ["cole o token do seu perfil no CDS", "paste the token from your CDS profile"],
  "s3.token_ph_set": ["token já configurado no servidor", "token already configured on the server"],
  "s3.token_hint": ["Gratuito em cds.climate.copernicus.eu → perfil → API Token. Aceite também os termos do AgERA5. O token fica só nesta máquina.",
    "Free at cds.climate.copernicus.eu → profile → API Token. Also accept the AgERA5 terms. The token stays on this machine."],
  "s3.token_hint_set": ["Há um token no config.json do servidor. Preencha só para usar outro.", "There is a token in the server's config.json. Fill this in only to use another one."],
  "s3.model": ["Modelo CMIP6", "CMIP6 model"],
  "s3.scenario": ["Cenário", "Scenario"],
  "s3.model_hint": ["Nem todo modelo tem todos os cenários; se faltar, a etapa de clima avisa.", "Not every model has every scenario; if one is missing, the climate step reports it."],
  "s3.res": ["Resolução da grade", "Grid resolution"],
  "s3.est_none": ["Defina a área para estimar o número de células.", "Define the area to estimate the number of cells."],
  "s3.est": ["<strong>~{cells} células</strong> × {years} ano(s). Simulação estimada em <strong>{time}</strong> com {workers} processo(s)",
    "<strong>~{cells} cells</strong> × {years} year(s). Simulation estimated at <strong>{time}</strong> with {workers} process(es)"],
  "s3.est_dl": [", mais o tempo de download", ", plus download time"],
  "s3.est_dl_cds": [" (AgERA5 depende da fila do CDS)", " (AgERA5 depends on the CDS queue)"],
  "s3.over_demo": ["A demonstração aceita até 3.000 células: aumente a resolução.", "The demo accepts up to 3,000 cells: use a coarser resolution."],
  "s3.over_real": ["Mais de {max} células: aumente a resolução ou reduza a área.", "More than {max} cells: use a coarser resolution or a smaller area."],
  "s3.bad_period": ["<strong>Período inválido.</strong> O ano inicial deve ser ≤ ao final, entre 1950 e 2100.", "<strong>Invalid period.</strong> The start year must be ≤ the end year, between 1950 and 2100."],
  "s3.src_demo": ["<strong>Demonstração:</strong> clima sintético gerado para {s}–{e}; nada é baixado.", "<strong>Demo:</strong> synthetic climate generated for {s}–{e}; nothing is downloaded."],
  "s3.src_agera5": ["<strong>AgERA5</strong> (reanálise, 0,1°, diário) via Copernicus CDS para {s}–{e}. Exige token.", "<strong>AgERA5</strong> (reanalysis, 0.1°, daily) via Copernicus CDS for {s}–{e}. Needs a token."],
  "s3.src_nex": ["<strong>NASA NEX-GDDP-CMIP6</strong> (0,25°, diário; histórico até 2014, depois o cenário SSP) para {s}–{e}. Sem token.", "<strong>NASA NEX-GDDP-CMIP6</strong> (0.25°, daily; historical to 2014, then the SSP scenario) for {s}–{e}. No token."],
  "s3.sum_invalid": ["período inválido", "invalid period"],
  "s3.sum_synth": ["sintético", "synthetic"],
  "s3.advanced": ["Opções avançadas", "Advanced options"],
  "s3.soilfix": ["<strong>Perfil de solo de 2 m alinhado ao SoilGrids.</strong> Sem ela, o AquaCrop usa 1,2 m e descarta a camada de 100–200 cm (comportamento original do toolchain).",
    "<strong>2 m soil profile aligned to SoilGrids.</strong> Without it, AquaCrop uses 1.2 m and drops the 100–200 cm layer (the toolchain's original behaviour)."],
  "s3.co2": ["<strong>CO₂ do cenário SSP escolhido.</strong> Sem ela, o AquaCrop usa a série Mauna Loa + A1B para qualquer cenário. Só muda projeções.",
    "<strong>CO₂ from the chosen SSP scenario.</strong> Without it, AquaCrop uses the Mauna Loa + A1B series for any scenario. Only affects projections."],
  "s3.cache": ["<strong>Reaproveitar os dados desta área.</strong> Guarda os recortes processados (pequenos) para que trocar a cultura não exija novo download. Os downloads brutos são sempre apagados ao final.",
    "<strong>Reuse this area's data.</strong> Keeps the (small) processed clips so changing the crop needs no new download. Raw downloads are always deleted at the end."],

  // ------------------------------------------------------------- step 4 --
  "s4.title": ["Executar", "Run"],
  "s4.inputs": ["Dados de entrada", "Input data"],
  "mode.real": ["Reais (download)", "Real (download)"],
  "mode.demo": ["Demonstração", "Demo"],
  "s4.guide_demo": ["Gera clima, solo, calendário e área de cultivo sintéticos em segundos e roda o AquaCrop real em cada célula. Serve para testar o fluxo e a interface; os números não representam a região.",
    "Generates synthetic climate, soil, calendar and crop area in seconds and runs the real AquaCrop in every cell. Use it to test the workflow and the interface; the numbers do not represent the region."],
  "s4.guide_real": ["Baixa SoilGrids, SPAM, GGCMI e o clima recortados para a área e roda o AquaCrop em cada célula. Na primeira vez numa área pode levar de minutos a horas (a fila do Copernicus é o gargalo). Os downloads brutos ficam numa pasta temporária, apagada ao final.",
    "Downloads SoilGrids, SPAM, GGCMI and climate clipped to the area and runs AquaCrop in every cell. The first run for an area can take minutes to hours (the Copernicus queue is the bottleneck). Raw downloads go to a temporary folder that is deleted at the end."],
  "s4.run": ["Rodar análise", "Run analysis"],
  "s4.running": ["Análise em andamento…", "Analysis running…"],
  "s4.block_area": ["Defina a área no passo 1.", "Define the area in step 1."],
  "s4.block_period": ["Corrija o período no passo 3.", "Fix the period in step 3."],
  "s4.block_token": ["Informe o token do Copernicus CDS no passo 3 ou use a demonstração.", "Enter the Copernicus CDS token in step 3 or use the demo."],
  "s4.cancel": ["Cancelar", "Cancel"],
  "s4.cancelling": ["Cancelando… a etapa em curso termina antes de parar.", "Cancelling… the current step finishes before stopping."],
  "s4.sent": ["Análise enviada.", "Analysis submitted."],
  "s4.log": ["Registro detalhado", "Detailed log"],
  "status.queued": ["Na fila", "Queued"],
  "status.running": ["Em execução", "Running"],
  "status.done": ["Concluída", "Finished"],
  "status.error": ["Falhou", "Failed"],
  "status.cancelled": ["Cancelada", "Cancelled"],
  "status.position": [" (posição {n})", " (position {n})"],

  // ------------------------------------------------------------ history --
  "hist.title": ["Análises anteriores", "Previous analyses"],
  "hist.cache": ["Cache", "Cache"],
  "hist.empty": ["Nenhuma ainda.", "None yet."],
  "hist.area": ["área", "area"],
  "hist.delete": ["Apagar análise", "Delete analysis"],
  "hist.confirm": ["Apagar esta análise e os arquivos dela?", "Delete this analysis and its files?"],

  // -------------------------------------------------------------- cache --
  "cache.title": ["Cache e temporários", "Cache and temporary files"],
  "cache.guide": ["Downloads brutos vão para uma pasta temporária apagada ao fim de cada análise. Ficam guardados só os arquivos globais (SPAM e GGCMI, iguais para qualquer área) e, se a opção estiver ligada, os recortes processados de cada área.",
    "Raw downloads go to a temporary folder deleted at the end of each analysis. Only the global files (SPAM and GGCMI, identical for any area) and, if enabled, each area's processed clips are kept."],
  "cache.global": ["Arquivos globais (SPAM, GGCMI)", "Global files (SPAM, GGCMI)"],
  "cache.areas": ["Recortes de {n} área(s)", "Clips of {n} area(s)"],
  "cache.tmp": ["Temporários em uso", "Temporary files in use"],
  "cache.folder": ["Pasta: {path}", "Folder: {path}"],
  "cache.clear_areas": ["Limpar recortes das áreas", "Clear area clips"],
  "cache.clear_global": ["Limpar arquivos globais", "Clear global files"],
  "cache.clear_all": ["Limpar tudo", "Clear everything"],
  "cache.cleared": ["Cache limpo.", "Cache cleared."],

  // ------------------------------------------------------------ results --
  "res.title": ["Resultados", "Results"],
  "res.sub_empty": ["Rode uma análise ou abra uma anterior.", "Run an analysis or open a previous one."],
  "res.empty": ["Quando a análise terminar, mapas, gráficos e arquivos aparecem aqui.", "When the analysis finishes, maps, charts and files appear here."],
  "res.download": ["Baixar", "Download"],
  "res.cells": ["{n} células", "{n} cells"],
  "res.drawn": ["Área desenhada", "Drawn area"],
  "res.open_failed": ["Não consegui abrir os resultados: {err}", "Could not open the results: {err}"],
  "res.demo_notice": ["Demonstração com dados sintéticos: o fluxo e o AquaCrop são reais, mas clima, solo, calendário e área são inventados. Não interprete estes números.",
    "Demo with synthetic data: the workflow and AquaCrop are real, but climate, soil, calendar and area are invented. Do not interpret these numbers."],
  "res.missing_years": ["Sem safra colhida em {years}. O ano de cada safra é o da colheita; safras plantadas no fim do período que não terminam até 31/12 do último ano não são simuladas, e a primeira colheita pode cair no ano seguinte ao início.",
    "No harvested season in {years}. Each season is dated by its harvest; seasons planted late in the period that do not finish by 31 Dec of the last year are not simulated, and the first harvest may fall in the year after the start."],
  "res.failed": ["{n} de {total} células sem resultado: {reasons}.", "{n} of {total} cells without a result: {reasons}."],
  "res.var": ["Variável no mapa", "Map variable"],
  "res.season": ["Safra", "Season"],
  "res.opacity": ["Opacidade", "Opacity"],
  "res.mean_period": ["Média do período", "Period mean"],
  "res.season_n": ["Safra {y}", "Season {y}"],
  "res.mean_short": ["média", "mean"],
  "res.cell_tip_area": ["{ha} ha de cultivo (SPAM)", "{ha} ha cropped (SPAM)"],
  "kpi.yield": ["Produtividade (matéria seca)", "Yield (dry matter)"],
  "kpi.scope_mean": ["média de {n} safra(s)", "mean of {n} season(s)"],
  "kpi.scope_one": ["safra {y}", "season {y}"],
  "kpi.gap": ["Lacuna hídrica", "Water-limited gap"],
  "kpi.gap_d": ["potencial − real", "potential − actual"],
  "kpi.et": ["Evapotranspiração no ciclo", "In-season evapotranspiration"],
  "kpi.et_d": ["chuva no ciclo {p} mm", "in-season rain {p} mm"],
  "kpi.wp": ["Produtividade da água", "Water productivity"],
  "kpi.wp_d": ["produtividade / ET", "yield / ET"],
  "kpi.prod": ["Produção estimada", "Estimated production"],
  "kpi.prod_d": ["{ha} ha (SPAM)", "{ha} ha (SPAM)"],
  "kpi.irr": ["Irrigação aplicada", "Applied irrigation"],
  "kpi.irr_d": ["gatilho a 80% da água disponível", "triggered at 80% of available water"],
  "ch.yield": ["Produtividade por safra", "Yield per season"],
  "ch.yield_sub": ["Média ponderada por {w}. Pontos: produtividade sem estresse hídrico; a diferença é a perda por falta de água.",
    "Mean weighted by {w}. Points: yield without water stress; the difference is the loss to water shortage."],
  "ch.yield_actual": ["Produtividade real", "Actual yield"],
  "ch.yield_pot": ["Potencial sem estresse hídrico", "Potential without water stress"],
  "ch.water": ["Balanço hídrico no ciclo", "In-season water balance"],
  "ch.water_sub": ["Destino da água entre o plantio e a maturação (média do domínio). A linha tracejada é a entrada de água no mesmo período.",
    "Where the water went between planting and maturity (domain mean). The dashed line is the water input over the same period."],
  "ch.water_axis": ["mm no ciclo", "mm in season"],
  "ch.tr": ["Transpiração", "Transpiration"],
  "ch.es": ["Evaporação do solo", "Soil evaporation"],
  "ch.ro": ["Escoamento", "Runoff"],
  "ch.dp": ["Percolação profunda", "Deep percolation"],
  "ch.rain_irr": ["Chuva + irrigação", "Rain + irrigation"],
  "ch.rain_season": ["Chuva no ciclo", "In-season rain"],
  "ch.hist": ["Distribuição entre células", "Distribution across cells"],
  "ch.hist_sub": ["{v}, {when}. Mostra a variabilidade espacial dentro da área.", "{v}, {when}. Shows the spatial variability within the area."],
  "ch.hist_when_mean": ["média do período", "period mean"],
  "ch.cells": ["células", "cells"],
  "ch.cells_title": ["Células", "Cells"],
  "ch.season": ["Safra", "Season"],
  "ch.date": ["Data", "Date"],
  "ch.expand": ["Expandir {t}", "Expand {t}"],
  "cell.title": ["Célula selecionada", "Selected cell"],
  "cell.empty": ["Clique numa célula do mapa para ver as séries diárias de dossel, biomassa, chuva e evapotranspiração.", "Click a cell on the map to see its daily canopy, biomass, rain and evapotranspiration series."],
  "cell.loading": ["Carregando célula {id}…", "Loading cell {id}…"],
  "cell.header": ["Célula {id} · {lat}, {lon}", "Cell {id} · {lat}, {lon}"],
  "cell.th_actual": ["Real t/ha", "Actual t/ha"],
  "cell.th_pot": ["Potencial t/ha", "Potential t/ha"],
  "cell.th_rain": ["Chuva mm", "Rain mm"],
  "cell.th_et": ["ET mm", "ET mm"],
  "cell.th_wp": ["WP kg/m³", "WP kg/m³"],
  "cell.cc": ["Cobertura do dossel", "Canopy cover"],
  "cell.cc_sub": ["Fração do solo coberta pelas folhas, só nos dias de lavoura.", "Fraction of ground covered by leaves, on crop days only."],
  "cell.bio": ["Biomassa acima do solo", "Above-ground biomass"],
  "cell.bio_sub": ["Acumulada ao longo de cada ciclo, em matéria seca.", "Accumulated over each cycle, as dry matter."],
  "cell.water": ["Chuva e evapotranspiração", "Rain and evapotranspiration"],
  "cell.water_sub": ["Entradas diárias de água contra a demanda atmosférica (ET0) e o consumo da lavoura.", "Daily water inputs against atmospheric demand (ET0) and crop water use."],
  "cell.wr": ["Água na zona radicular", "Root-zone water"],
  "cell.wr_sub": ["Conteúdo de água no volume de solo explorado pelas raízes.", "Water held in the soil volume explored by the roots."],
  "cell.rain": ["Chuva", "Rain"],
  "cell.irr": ["Irrigação", "Irrigation"],
  "cell.eta": ["ET real (Tr + Es)", "Actual ET (Tr + Es)"],
  "cell.et0": ["ET de referência", "Reference ET"],
  "unit.mm_day": ["mm/dia", "mm/day"],
  "unit.days": ["dias", "days"],
  "about.title": ["Sobre esta análise", "About this analysis"],
  "about.sources": ["Clima: {clim}. Solo: {soil}. Calendário: {cal}. Área de cultivo: {area}.", "Climate: {clim}. Soil: {soil}. Calendar: {cal}. Crop area: {area}."],
  "about.synthetic": ["sintético (demonstração)", "synthetic (demo)"],
  "about.synthetic_short": ["sintético", "synthetic"],
  "about.model": ["Modelo: AquaCrop-OSPy, uma simulação independente por célula (geoaquacrop_simulate), parâmetros padrão da cultura com o ciclo ajustado ao calendário local.",
    "Model: AquaCrop-OSPy, one independent simulation per cell (geoaquacrop_simulate), default crop parameters with the cycle adjusted to the local calendar."],
  "about.dating": ["O ano de cada safra é o da colheita. Produtividades em matéria seca (t/ha).", "Each season is dated by its harvest year. Yields are dry matter (t/ha)."],
  "about.weighting": ["Médias do domínio ponderadas por {w}.", "Domain means weighted by {w}."],
  "about.seasonal": ["Evapotranspiração, chuva e produtividade da água são somadas por safra a partir da saída diária (do plantio à maturação). As colunas equivalentes do toolchain somam o período inteiro e repetem o total em todas as safras.",
    "Evapotranspiration, rain and water productivity are summed per season from the daily output (planting to maturity). The toolchain's equivalent columns sum the whole period and repeat that total for every season."],
  "about.patches": ["Correções aplicadas: {list}.", "Corrections applied: {list}."],
  "about.no_patches": ["Sem correções: AquaCrop configurado como no toolchain original.", "No corrections: AquaCrop set up as in the original toolchain."],
  "about.patch_soil": ["perfil de solo de 2 m alinhado ao SoilGrids", "2 m soil profile aligned to SoilGrids"],
  "about.patch_co2": ["CO₂ do cenário {s}", "CO₂ from scenario {s}"],
  "about.id": ["Análise {id}.", "Analysis {id}."],
  "w.crop_area": ["área de cultivo (SPAM)", "crop area (SPAM)"],
  "w.cell_area": ["área da célula (cos lat)", "cell area (cos lat)"],
  "files.seasons": ["Tabela por célula e safra: produtividade, balanço hídrico, WP", "Table per cell and season: yield, water balance, WP"],
  "files.grid": ["Grade NetCDF (ano, y, x) das principais variáveis, para SIG", "NetCDF grid (year, y, x) of the main variables, for GIS"],
  "files.cells": ["Células como polígonos com atributos por ano (abre no QGIS)", "Cells as polygons with per-year attributes (opens in QGIS)"],
  "files.daily": ["Séries diárias de todas as células (NetCDF compactado)", "Daily series of every cell (compressed NetCDF)"],
  "files.aoi": ["Polígono usado na análise (EPSG:4326)", "Polygon used in the analysis (EPSG:4326)"],

  // -------------------------------------------------------------- modal --
  "modal.csv": ["Baixar CSV", "Download CSV"],
  "modal.close": ["Fechar", "Close"],
  "modal.table": ["Ver tabela", "Show table"],
  "modal.rows": ["Mostrando 3.000 de {n} linhas; o CSV tem todas.", "Showing 3,000 of {n} rows; the CSV has them all."],
  "api.offline": ["Sem conexão com o servidor do GeoAquaCrop. Ele ainda está rodando?", "No connection to the GeoAquaCrop server. Is it still running?"],
  "api.error": ["Erro {status}", "Error {status}"],

  // ------------------------------------------------------------ map --
  "bm.esri_sat": ["Satélite (Esri)", "Satellite (Esri)"],
  "bm.esri_topo": ["Topográfico (Esri)", "Topographic (Esri)"],
  "bm.osm": ["OpenStreetMap", "OpenStreetMap"],
  "bm.carto": ["Claro (Carto)", "Light (Carto)"],
  "bm.google": ["Satélite (Google)", "Satellite (Google)"],
  "bm.labels": ["Rótulos e limites", "Labels and boundaries"],
  "map.attr_esri": ["Imagens © Esri, Maxar, Earthstar Geographics", "Imagery © Esri, Maxar, Earthstar Geographics"],
  "map.attr_osm": ["© colaboradores do OpenStreetMap", "© OpenStreetMap contributors"],

  "draw.poly_start": ["Clique para começar o polígono.", "Click to start drawing the polygon."],
  "draw.poly_cont": ["Clique para continuar o polígono.", "Click to continue drawing the polygon."],
  "draw.poly_end": ["Clique no primeiro ponto para fechar.", "Click the first point to close the shape."],
  "draw.rect_start": ["Clique e arraste para desenhar o retângulo.", "Click and drag to draw the rectangle."],
  "draw.shape_end": ["Solte o mouse para terminar.", "Release the mouse to finish."],
  "draw.intersect": ["As arestas não podem se cruzar.", "Shape edges cannot cross."],

  // ------------------------------------------------------------ credits --
  "cr.title": ["Créditos", "Credits"],
  "cr.intro": ["Esta é a interface web (WebGIS) do <strong>GeoAquaCrop</strong>, o conjunto de ferramentas que roda o AquaCrop-OSPy em grade sobre grandes regiões a partir de dados globais abertos. O pré-processamento e a simulação vêm dos pacotes do GeoAquaCrop, desenvolvidos por:",
    "This is the web interface (WebGIS) for <strong>GeoAquaCrop</strong>, the toolchain that runs AquaCrop-OSPy in gridded form over large regions from open global data. Preprocessing and simulation come from the GeoAquaCrop packages, developed by:"],
  "cr.maintainer": ["mantenedor do geoaquacrop_simulate", "maintainer of geoaquacrop_simulate"],
  "cr.cite": ["Como citar", "How to cite"],
  "cr.cite_text": ["Ao publicar resultados, cite o GeoAquaCrop e o AquaCrop-OSPy. Enquanto o preprint não sai, os autores pedem:",
    "When publishing results, cite GeoAquaCrop and AquaCrop-OSPy. Until the preprint is out, the authors ask for:"],
  "cr.preprint": ["(preprint em preparação)", "(preprint in preparation)"],
  "cr.model": ["Modelo", "Model"],
  "cr.data": ["Dados", "Data"],
  "cr.data_text": ["Clima AgERA5 (Copernicus C3S, Boogaard et al. 2020) e NASA NEX-GDDP-CMIP6 (Thrasher et al. 2022); solo SoilGrids 2.0 (ISRIC, Poggio et al. 2021); calendário GGCMI fase 3 (Jägermeyr et al. 2021) e MARC (Zhao et al. 2024); áreas de cultivo SPAM (IFPRI, Yu et al. 2020). Cite também as fontes de dados usadas.",
    "Climate AgERA5 (Copernicus C3S, Boogaard et al. 2020) and NASA NEX-GDDP-CMIP6 (Thrasher et al. 2022); soil SoilGrids 2.0 (ISRIC, Poggio et al. 2021); crop calendar GGCMI phase 3 (Jägermeyr et al. 2021) and MARC (Zhao et al. 2024); crop areas SPAM (IFPRI, Yu et al. 2020). Please cite the data sources used too."],
  "cr.map": ["Mapa e software", "Map and software"],
  "cr.map_text": ["Mapas de fundo Esri, OpenStreetMap e CARTO; busca OpenStreetMap Nominatim. Leaflet, Leaflet.draw, Chart.js, FastAPI e a fonte Public Sans.",
    "Basemaps by Esri, OpenStreetMap and CARTO; search by OpenStreetMap Nominatim. Leaflet, Leaflet.draw, Chart.js, FastAPI and the Public Sans typeface."],
  "cr.licence": ["GeoAquaCrop e AquaCrop-OSPy são distribuídos sob a licença Apache-2.0.", "GeoAquaCrop and AquaCrop-OSPy are distributed under the Apache-2.0 licence."],
};

const CROPS = {
  Maize: ["Milho", "Maize"], Soybean: ["Soja", "Soybean"], Wheat_winter: ["Trigo de inverno", "Winter wheat"],
  Wheat_summer: ["Trigo de primavera", "Spring wheat"], Barley: ["Cevada", "Barley"], Sorghum: ["Sorgo", "Sorghum"],
  Cotton: ["Algodão", "Cotton"], DryBean: ["Feijão", "Dry bean"], PaddyRice1: ["Arroz (1ª safra)", "Rice (1st season)"],
  PaddyRice2: ["Arroz (2ª safra)", "Rice (2nd season)"], Potato: ["Batata", "Potato"], Cassava: ["Mandioca", "Cassava"],
  SugarCane: ["Cana-de-açúcar", "Sugarcane"], SugarBeet: ["Beterraba açucareira", "Sugar beet"], Sunflower: ["Girassol", "Sunflower"],
};
const SSPS = {
  ssp126: ["SSP1-2.6 (baixas emissões)", "SSP1-2.6 (low emissions)"],
  ssp245: ["SSP2-4.5 (intermediário)", "SSP2-4.5 (intermediate)"],
  ssp370: ["SSP3-7.0 (altas emissões)", "SSP3-7.0 (high emissions)"],
  ssp585: ["SSP5-8.5 (muito altas)", "SSP5-8.5 (very high)"],
};
const VARS = {
  yield_dry: ["Produtividade (matéria seca)", "Yield (dry matter)"],
  yield_pot: ["Produtividade potencial (sem estresse hídrico)", "Potential yield (no water stress)"],
  yield_gap: ["Lacuna hídrica de produtividade (potencial − real)", "Water-limited yield gap (potential − actual)"],
  production_t: ["Produção (produtividade × área SPAM)", "Production (yield × SPAM area)"],
  precip_mm: ["Precipitação no ciclo", "In-season precipitation"],
  et_mm: ["Evapotranspiração no ciclo (Tr + Es)", "In-season evapotranspiration (Tr + Es)"],
  irrigation_mm: ["Irrigação aplicada", "Applied irrigation"],
  deep_perc_mm: ["Percolação profunda", "Deep percolation"],
  runoff_mm: ["Escoamento superficial", "Surface runoff"],
  wp_et: ["Produtividade da água (produtividade / ET)", "Water productivity (yield / ET)"],
  season_length: ["Duração do ciclo", "Season length"],
};

const LANGS = ["pt", "en"];
let lang = "pt";

function detect() {
  try {
    const saved = localStorage.getItem("geocrop.lang");
    if (LANGS.includes(saved)) return saved;
  } catch { /* storage unavailable */ }
  return (navigator.language || "pt").toLowerCase().startsWith("pt") ? "pt" : "en";
}

export function getLang() { return lang; }
export function locale() { return lang === "pt" ? "pt-BR" : "en-GB"; }

function pick(entry) { return entry ? entry[LANGS.indexOf(lang)] : undefined; }

export function t(key, vars = {}) {
  const s = pick(D[key]);
  if (s === undefined) return key;
  return s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? `{${k}}`));
}
export const cropName = (id) => pick(CROPS[id]) || id;
export const sspName = (id) => pick(SSPS[id]) || id;
export const varName = (id, fallback) => pick(VARS[id]) || fallback || id;
export const unitName = (u) => (u === "dias" || u === "days" ? t("unit.days") : u === "kg/m3" ? "kg/m³" : u);

export function applyDOM(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  root.querySelectorAll("[data-i18n-html]").forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
  root.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
  root.querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
  document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
  document.querySelectorAll("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.lang === lang));
}

export function setLang(next) {
  if (!LANGS.includes(next) || next === lang) return;
  lang = next;
  try { localStorage.setItem("geocrop.lang", lang); } catch { /* ignore */ }
  applyDOM();
  window.dispatchEvent(new CustomEvent("langchange", { detail: lang }));
}

export function initLang() {
  lang = detect();
  applyDOM();
}

// Server step messages: translate from key + args when available.
const MSG = {
  "msg.area_done": ["{area} km² · ~{n} células de {res}°", "{area} km² · ~{n} cells of {res}°"],
  "msg.synthetic_start": ["valores inventados, só para testar o fluxo", "invented values, only to test the workflow"],
  "msg.cache_reused": ["reaproveitado do cache da área", "reused from the area cache"],
  "msg.climate_agera5": ["AgERA5 via Copernicus CDS (a fila do CDS pode levar de minutos a horas)", "AgERA5 via Copernicus CDS (the CDS queue can take minutes to hours)"],
  "msg.climate_nex": ["NASA NEX-GDDP-CMIP6 · {model} · {ssp}", "NASA NEX-GDDP-CMIP6 · {model} · {ssp}"],
  "msg.sim_validating": ["validando entradas", "validating inputs"],
  "msg.sim_start": ["0 de {n} células · {workers} processos", "0 of {n} cells · {workers} processes"],
  "msg.sim_progress": ["{done} de {n} células · ~{eta} restantes", "{done} of {n} cells · ~{eta} left"],
  "msg.sim_done": ["{ok} células simuladas em {elapsed}", "{ok} cells simulated in {elapsed}"],
  "msg.sim_done_failed": ["{ok} células simuladas, {failed} sem resultado, em {elapsed}", "{ok} cells simulated, {failed} without result, in {elapsed}"],
  "msg.results_done": ["{n} safra(s)", "{n} season(s)"],
  "msg.cleanup_done": ["{mb} MB de temporários removidos", "{mb} MB of temporary files removed"],
  "msg.cancelled": ["cancelado", "cancelled"],
};
const STEPS = {
  area: ["Preparar a área", "Prepare the area"], soil: ["Solo (SoilGrids)", "Soil (SoilGrids)"],
  crop_areas: ["Áreas de cultivo (SPAM)", "Crop areas (SPAM)"], crop_calendar: ["Calendário agrícola (GGCMI)", "Crop calendar (GGCMI)"],
  climate: ["Clima", "Climate"], synthetic: ["Gerar dados sintéticos", "Generate synthetic data"],
  simulate: ["Simulação AquaCrop por célula", "AquaCrop simulation per cell"], results: ["Montar resultados", "Build results"],
  cleanup: ["Limpar temporários", "Remove temporary files"],
};
export const stepName = (key, fallback) => pick(STEPS[key]) || fallback || key;
export function stepMessage(step, fmtNum, fmtDur) {
  if (!step.msg_key || !MSG[step.msg_key]) return step.message || "";
  const a = { ...(step.msg_args || {}) };
  for (const k of ["n", "done", "ok", "failed", "area"]) if (typeof a[k] === "number") a[k] = fmtNum(a[k], 0);
  if (typeof a.mb === "number") a.mb = fmtNum(a.mb, 1);
  for (const k of ["eta", "elapsed"]) if (typeof a[k] === "number") a[k] = fmtDur(a[k]);
  return pick(MSG[step.msg_key]).replace(/\{(\w+)\}/g, (_, k) => (a[k] ?? `{${k}}`));
}
