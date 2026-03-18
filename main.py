#!/usr/bin/env python3
"""BioScale — Body Composition via BLE"""
import argparse
import webbrowser
import threading
import logging
import asyncio

def configure_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description='BioScale')
    parser.add_argument('--port', type=int, default=8050)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--scan', action='store_true', help='Apenas scan BLE')
    args = parser.parse_args()

    configure_logging(args.debug)
    logger = logging.getLogger(__name__)

    # Inicializar banco de dados
    from database.db import init_db
    logger.info("Verificando banco de dados...")
    init_db()
    
    # Executar apenas o scan BLE se solicitado
    if args.scan:
        logger.info("Executando scan BLE apenas...")
        from ble.scanner import scan_for_scale
        devices = asyncio.run(scan_for_scale(timeout=10.0))
        if not devices:
            print("Nenhuma balança encontrada.")
        else:
            print(f"{len(devices)} balança(s) encontrada(s):")
            for d in devices:
                print(f"- {d['name']} [{d['address']}] (RSSI: {d['rssi']} dBm) PROTO: {d['protocol_hint']}")
        return

    # Iniciar o servidor de Dashboard
    logger.info("Iniciando Dashboard...")
    from dashboard.index import app
    
    if not args.no_browser:
        # Abrir o browser após um delay
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(f'http://localhost:{args.port}')
        threading.Thread(target=open_browser, daemon=True).start()

    # Roda o servidor single thread nativo (usar waitress para produção, mas app.run atende p/ desktop dev)
    app.run(host='127.0.0.1' if not args.debug else '0.0.0.0', port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
