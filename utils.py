from os.path import dirname, realpath

from argparse_to_json import convert_parser_to_json


CUR_DIR = dirname(realpath(__file__))


def do_format(entry, is_check=False):
    assert (isinstance(entry, dict))

    list_type = "check" if is_check else "list"

    if "enum" in entry:
        r = {list_type: entry["enum"]}
    elif entry["type"] == "string":
        r = {list_type: [entry["default"]]}
    elif entry["type"] == "integer":
        r = {"field": entry["default"]}
    else:
        r = None
    return r


def extract(parser):
    values = vars(parser.parse_args())
    json_data = convert_parser_to_json(parser)
    for k, v in values.items():
        json_data["schema"][k]["default"] = v
    return json_data


def setup_preset(predefined_args, preset, ignored_params):
    """ Assigning predefined settings.
    """
    for p, v in preset.items():
        if p in ignored_params:
            continue
        target = predefined_args[p]
        if "list" in target:
            target['list'].remove(v)
            # Place element in the beginning
            target['list'].insert(0, v)
        if "integer" in target:
            target["field"] = v
        if "string" in target:
            target["list_type"][0] = v
