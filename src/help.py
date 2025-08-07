HELP = """Patchbay application for JACK
Usage: patchance [--help] [--version]
  --config-dir CONFIG_DIR, -c CONFIG_DIR
            use a custom config directory
  --export-custom-names, -c2p
            export custom names from config to JACK pretty-names and exit
  --import-pretty-names, -p2c
            import JACK pretty-names to custom names, save config and exit
  --clear-pretty-names
            delete all JACK pretty-name metadatas and exit
  --dbg, -dbg
            log debug for modules splitted with a ':',
            for example: --dbg patch_engine:patchbay.patchcanvas
  --info, -info MODULES
            log infos for modules splitted with a ':',
            for example: --info patch_engine:patchbay.patchcanvas
  --help     show this help
  --version  print program version
"""
