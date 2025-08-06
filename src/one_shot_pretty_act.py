import json
from pathlib import Path
import sys

# add HoustonPatchbay as lib
sys.path.insert(1, str(Path(__file__).parents[1] / 'HoustonPatchbay/source'))

from patch_engine import PatchEngine, PatchEngineOuter


def make_one_shot_act(arg: str, config_dir: Path):
    canvas_path = config_dir / 'canvas.json'
    if canvas_path.is_file():
        try:
            with open(canvas_path) as f:
                json_patch = json.load(f)
        except:
            sys.exit(1)
    else:
        sys.exit(0)    
    
    patch_engine = PatchEngine('PatchanceExport')
    patch_engine.custom_names.eat_json(json_patch['custom_names'])
    patch_engine.start(PatchEngineOuter())
    
    match arg:
        case '--export-custom-names'|'-c2p':
            patch_engine.export_all_custom_names_to_jack_now()

        case '--import-pretty-names'|'-p2c':
            custom_names = patch_engine.custom_names
            clients_dict, ports_dict = \
                patch_engine.import_all_pretty_names_from_jack()
            for client_name, pretty_name in clients_dict.items():
                custom_names.save_group(client_name, pretty_name)
            for port_name, pretty_name in ports_dict.items():
                custom_names.save_port(port_name, pretty_name)

            json_patch['custom_names'] = custom_names.to_json()
            try:
                with open(canvas_path, 'w') as f:
                    json.dump(json_patch, f)
            except:
                sys.stderr.write(f'Failed to save {canvas_path} file')
        
        case '--clear-pretty-names':
            patch_engine.clear_all_pretty_names_from_jack()
    
    patch_engine.exit()
    sys.exit(0)