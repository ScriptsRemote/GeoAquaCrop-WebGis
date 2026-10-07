"""Start the GeoAquaCrop WebGIS:  python run.py   then open http://127.0.0.1:8050

The ``__main__`` guard matters: on Windows the simulation's worker processes
re-import this file, and must not start a second server.
"""
import sys
import webbrowser
from pathlib import Path
from threading import Timer

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))


def main():
    import uvicorn

    from geocrop.settings import settings

    url = f"http://{settings.host}:{settings.port}"
    print(f"\n  GeoAquaCrop em {url}  (Ctrl+C para parar)\n")
    if "--no-browser" not in sys.argv:
        Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run("geocrop.app:app", host=settings.host, port=settings.port, log_level="warning")


if __name__ == "__main__":
    main()
