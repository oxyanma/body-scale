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
    parser.add_argument('--scan', action='store_true', help='BLE scan only')
    args = parser.parse_args()

    configure_logging(args.debug)
    logger = logging.getLogger(__name__)

    # Initialize database
    from database.db import init_db
    logger.info("Checking database...")
    init_db()
    
    # Run BLE scan only if requested
    if args.scan:
        logger.info("Running BLE scan only...")
        from ble.scanner import scan_for_scale
        devices = asyncio.run(scan_for_scale(timeout=10.0))
        if not devices:
            print("No scale found.")
        else:
            print(f"{len(devices)} scale(s) found:")
            for d in devices:
                print(f"- {d['name']} [{d['address']}] (RSSI: {d['rssi']} dBm) PROTO: {d['protocol_hint']}")
        return

    # Start Dashboard server
    logger.info("Starting Dashboard...")
    from dashboard.index import app
    
    if not args.no_browser:
        # Open browser after a delay
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(f'http://localhost:{args.port}')
        threading.Thread(target=open_browser, daemon=True).start()

    # Run native single-thread server (use waitress for prod, app.run is fine for desktop dev)
    app.run(host='127.0.0.1' if not args.debug else '0.0.0.0', port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
