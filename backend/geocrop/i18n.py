"""Server-side messages in Portuguese and English.

The interface sends its language in the ``X-Lang`` header; analyses remember
the language they were started in (``params['lang']``) for their log lines.
Step progress is also stored as a message key + arguments, so the interface
can show it in whichever language is selected now.
"""
from __future__ import annotations

LANGS = ("pt", "en")
DEFAULT = "pt"

M = {
    # ------------------------------------------------------------ steps --
    "step.area": ("Preparar a área", "Prepare the area"),
    "step.soil": ("Solo (SoilGrids)", "Soil (SoilGrids)"),
    "step.crop_areas": ("Áreas de cultivo (SPAM)", "Crop areas (SPAM)"),
    "step.crop_calendar": ("Calendário agrícola (GGCMI)", "Crop calendar (GGCMI)"),
    "step.climate": ("Clima", "Climate"),
    "step.synthetic": ("Gerar dados sintéticos", "Generate synthetic data"),
    "step.simulate": ("Simulação AquaCrop por célula", "AquaCrop simulation per cell"),
    "step.results": ("Montar resultados", "Build results"),
    "step.cleanup": ("Limpar temporários", "Remove temporary files"),

    # ---------------------------------------------------- step messages --
    "msg.area_done": ("{area} km² · ~{n} células de {res}°", "{area} km² · ~{n} cells of {res}°"),
    "msg.synthetic_start": ("valores inventados, só para testar o fluxo",
                            "invented values, only to test the workflow"),
    "msg.cache_reused": ("reaproveitado do cache da área", "reused from the area cache"),
    "msg.climate_agera5": ("AgERA5 via Copernicus CDS (a fila do CDS pode levar de minutos a horas)",
                           "AgERA5 via Copernicus CDS (the CDS queue can take minutes to hours)"),
    "msg.climate_nex": ("NASA NEX-GDDP-CMIP6 · {model} · {ssp}", "NASA NEX-GDDP-CMIP6 · {model} · {ssp}"),
    "msg.sim_validating": ("validando entradas", "validating inputs"),
    "msg.sim_start": ("0 de {n} células · {workers} processos", "0 of {n} cells · {workers} processes"),
    "msg.sim_progress": ("{done} de {n} células · ~{eta} restantes", "{done} of {n} cells · ~{eta} left"),
    "msg.sim_done": ("{ok} células simuladas em {elapsed}", "{ok} cells simulated in {elapsed}"),
    "msg.sim_done_failed": ("{ok} células simuladas, {failed} sem resultado, em {elapsed}",
                            "{ok} cells simulated, {failed} without result, in {elapsed}"),
    "msg.results_done": ("{n} safra(s)", "{n} season(s)"),
    "msg.cleanup_done": ("{mb} MB de temporários removidos", "{mb} MB of temporary files removed"),
    "msg.cancelled": ("cancelado", "cancelled"),

    # ------------------------------------------------------------- log ---
    "log.cancelled": ("Análise cancelada.", "Analysis cancelled."),
    "log.cleanup_failed": ("Falha ao limpar temporários: {err}", "Could not remove temporary files: {err}"),
    "log.synthetic_grid": ("Gerando dados sintéticos para {n} células ({ny}×{nx} grade, {res}°)",
                           "Generating synthetic data for {n} cells ({ny}×{nx} grid, {res}°)"),
    "log.synthetic_climate": ("Clima sintético escrito (Tmin, Tmax, precipitação, ET0 Hargreaves)",
                              "Synthetic climate written (Tmin, Tmax, precipitation, Hargreaves ET0)"),
    "log.synthetic_soil": ("Solo sintético escrito (6 camadas, textura e matéria orgânica)",
                           "Synthetic soil written (6 layers, texture and organic matter)"),
    "log.synthetic_calendar": ("Calendário sintético: plantio ~DOY {doy}, ciclo ~{gsl} dias",
                               "Synthetic calendar: planting ~DOY {doy}, cycle ~{gsl} days"),
    "log.synthetic_area": ("Área de cultivo sintética escrita (SPAM {year})",
                           "Synthetic crop area written (SPAM {year})"),

    # ---------------------------------------------------------- errors ---
    "err.restart": ("Interrompido: o servidor foi reiniciado durante a execução.",
                    "Interrupted: the server was restarted while this was running."),
    "err.step_no_output": ("A etapa '{step}' terminou sem gerar {files}.",
                           "Step '{step}' finished without producing {files}."),
    "err.no_cells": ("Nenhuma célula com dados de clima dentro da área.",
                     "No cell with climate data inside the area."),
    "err.too_many_cells_run": ("{n} células excedem o limite de {max}. Use uma resolução mais grossa ou uma área "
                               "menor (o limite fica em config.json → max_cells).",
                               "{n} cells exceed the limit of {max}. Use a coarser resolution or a smaller area "
                               "(the limit is config.json → max_cells)."),
    "err.no_result": ("Nenhuma célula produziu resultado. Motivos: {reasons}",
                      "No cell produced a result. Reasons: {reasons}"),
    "err.unknown_crop": ("Cultura desconhecida: {crop}", "Unknown crop: {crop}"),
    "err.years_order": ("O ano inicial deve ser menor ou igual ao final.",
                        "The start year must be less than or equal to the end year."),
    "err.years_range": ("Os anos devem estar entre 1950 e 2100.", "Years must be between 1950 and 2100."),
    "err.resolution": ("Resolução inválida.", "Invalid resolution."),
    "err.no_aoi": ("Defina a área de interesse.", "Define the area of interest."),
    "err.token": ("Para anos passados o clima vem do AgERA5 e exige o token da API do Copernicus CDS "
                  "(perfil em cds.climate.copernicus.eu).",
                  "For past years the climate comes from AgERA5 and needs a Copernicus CDS API token "
                  "(profile at cds.climate.copernicus.eu)."),
    "err.too_many_cells": ("~{n} células excede o limite de {max}. Aumente a resolução (ex.: 0,1°) ou reduza a área.",
                           "~{n} cells exceeds the limit of {max}. Use a coarser resolution (e.g. 0.1°) or a smaller area."),
    "err.demo_cells": ("~{n} células: a demonstração aceita até 3.000. Use resolução mais grossa ou área menor.",
                       "~{n} cells: the demo accepts up to 3,000. Use a coarser resolution or a smaller area."),
    "err.job_not_found": ("Análise não encontrada.", "Analysis not found."),
    "err.cancel_first": ("Cancele a análise antes de apagar.", "Cancel the analysis before deleting it."),
    "err.results_not_ready": ("Resultados ainda não disponíveis.", "Results are not available yet."),
    "err.aoi_not_found": ("Área não encontrada.", "Area not found."),
    "err.daily_missing": ("Séries diárias não disponíveis.", "Daily series are not available."),
    "err.cell_missing": ("Célula sem resultado.", "Cell has no result."),
    "err.file_missing": ("Arquivo não encontrado.", "File not found."),
    "err.cache_busy": ("Há uma análise em execução; limpe o cache depois.",
                       "An analysis is running; clear the cache afterwards."),
    "err.cache_scope": ("scope deve ser areas, global ou all", "scope must be areas, global or all"),
    "err.search": ("A busca de lugares (OpenStreetMap Nominatim) não respondeu: {err}",
                   "Place search (OpenStreetMap Nominatim) did not respond: {err}"),
    "err.geometry": ("Geometria inválida: {err}", "Invalid geometry: {err}"),

    # ------------------------------------------------------------- AOI ---
    "aoi.too_big": ("Arquivo maior que 50 MB. Simplifique a geometria antes de enviar.",
                    "File larger than 50 MB. Simplify the geometry before uploading."),
    "aoi.unsupported": ("Formato {ext} não suportado. Use GeoJSON, KML, KMZ, GeoPackage ou shapefile compactado (.zip).",
                        "Format {ext} is not supported. Use GeoJSON, KML, KMZ, GeoPackage or a zipped shapefile (.zip)."),
    "aoi.no_ext": ("(sem extensão)", "(no extension)"),
    "aoi.bad_geojson": ("GeoJSON inválido ({err}).", "Invalid GeoJSON ({err})."),
    "aoi.geojson_empty": ("GeoJSON sem geometrias reconhecíveis.", "GeoJSON without recognisable geometries."),
    "aoi.bad_kml": ("O KML não pôde ser lido ({err}).", "The KML could not be read ({err})."),
    "aoi.kml_no_polygon": ("Nenhum polígono encontrado no KML. Linhas e pontos não definem uma área: desenhe ou "
                           "exporte um polígono.",
                           "No polygon found in the KML. Lines and points do not define an area: draw or "
                           "export a polygon."),
    "aoi.bad_kmz": ("KMZ corrompido (não é um zip válido).", "Corrupted KMZ (not a valid zip)."),
    "aoi.kmz_no_kml": ("O KMZ não contém nenhum arquivo .kml.", "The KMZ contains no .kml file."),
    "aoi.bad_zip": ("Zip corrompido.", "Corrupted zip."),
    "aoi.zip_paths": ("Zip com caminhos inválidos.", "Zip with invalid paths."),
    "aoi.zip_no_shp": ("O zip não contém um shapefile (.shp com .shx, .dbf e .prj).",
                       "The zip contains no shapefile (.shp with .shx, .dbf and .prj)."),
    "aoi.shp_incomplete": ("Shapefile incompleto: faltam {missing}.", "Incomplete shapefile: missing {missing}."),
    "aoi.unreadable": ("Não consegui ler o arquivo: {err}", "Could not read the file: {err}"),
    "aoi.no_crs": ("O arquivo não declara sistema de coordenadas; assumi WGS84 (EPSG:4326). Confira se a área "
                   "caiu no lugar certo.",
                   "The file declares no coordinate system; WGS84 (EPSG:4326) was assumed. Check that the area "
                   "landed in the right place."),
    "aoi.reprojected": ("Reprojetado de {crs} para WGS84 (EPSG:4326).", "Reprojected from {crs} to WGS84 (EPSG:4326)."),
    "aoi.dropped": ("{n} geometria(s) que não são polígonos foram ignoradas.",
                    "{n} non-polygon geometry(ies) were ignored."),
    "aoi.no_polygon": ("Nenhum polígono válido. A área precisa ser um polígono, não uma linha ou um ponto.",
                       "No valid polygon. The area must be a polygon, not a line or a point."),
    "aoi.fixed": ("Geometria com autointerseção foi corrigida automaticamente.",
                  "A self-intersecting geometry was repaired automatically."),
    "aoi.empty": ("A geometria resultante está vazia.", "The resulting geometry is empty."),
    "aoi.not_degrees": ("Coordenadas fora de longitude/latitude. O arquivo provavelmente está em UTM sem .prj; "
                        "exporte em EPSG:4326.",
                        "Coordinates are not longitude/latitude. The file is probably in UTM without a .prj; "
                        "export it in EPSG:4326."),
    "aoi.small": ("Área com menos de 0,25° de lado (~25 km). Os dados de clima têm 0,1–0,25° de resolução: o "
                  "resultado será pouco detalhado e a etapa de clima pode falhar.",
                  "Area smaller than 0.25° across (~25 km). Climate data have 0.1–0.25° resolution: results "
                  "will be coarse and the climate step may fail."),
    "aoi.simplified": ("Contorno com {n} vértices simplificado (tolerância ~100 m).",
                       "Outline with {n} vertices simplified (~100 m tolerance)."),
}


def norm(lang: str | None) -> str:
    lang = (lang or "").lower()[:2]
    return lang if lang in LANGS else DEFAULT


def tr(key: str, lang: str | None = None, **kw) -> str:
    entry = M.get(key)
    if entry is None:
        return key
    text = entry[LANGS.index(norm(lang))]
    try:
        return text.format(**kw)
    except (KeyError, IndexError):
        return text


def fmt_duration(seconds: float, lang: str | None = None) -> str:
    seconds = int(max(seconds, 0))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}min {seconds % 60:02d}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60:02d}min"


def fmt_int(n, lang: str | None = None) -> str:
    s = f"{int(n):,}"
    return s.replace(",", ".") if norm(lang) == "pt" else s
