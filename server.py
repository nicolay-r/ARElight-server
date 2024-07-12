from flask import Flask, request, render_template_string, jsonify
from threading import Thread
import os
import json
import subprocess

from arelight.arekit.sample_service import AREkitSamplesService
from os.path import join, dirname, realpath
from tqdm import tqdm

from flask_cors import CORS


ARELIGHT_IS_RUNNING = False

cur_dir = dirname(realpath(__file__))

SETTINGS = {
    "installed_arelight": "arelight.run.infer",
    "path_to_raw_data": join(cur_dir, r"raw_data"),
    "path_to_arelight_log": join(cur_dir, r"arelight.log"),
    "path_to_force_data": join(cur_dir, r"output", r"force"),
    "path_to_radial_data": join(cur_dir, r"output", r"radial"),
    "arelight_const_args": {
        "sampling-framework": "arekit"
    },
    "arelight_args": {
        "ner-model-name": {"list": ["ner_ontonotes_bert"]},
        "ner-types": {"check": ["ORG", "PERSON", "LOC", "GPE"]},
        "terms-per-context": {"field": 50},
        "sentence-parser": {"list": ["nltk:russian"]},
        "text-b-type": {"list": ["nli_m"]},
        "tokens-per-context": {"field": 128},
        "bert-framework": {"list": ["opennre"]},
        "batch-size": {"field": 10},
        "stemmer": {"list": ["mystem"]},
        "inference-writer": {"list": ["sqlite3"]},
        "pretrained-bert": {"list": ["DeepPavlov/rubert-base-cased"]},
        "bert-torch-checkpoint": {"list": ["ra4-rsr1_DeepPavlov-rubert-base-cased_cls.pth.tar"]},
        "backend": {"list": ["d3js_graphs"]}
    }
}

data_status_file = 'data_status.json'

# app = Flask(__name__)
app = Flask("ARElight-main")
CORS(app)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)


def generate_ARELIGHT_PARAMETERS():
    html_code = ""
    for parameter_name, parameter_info in SETTINGS["arelight_args"].items():
        if "const" in parameter_info:
            # Generate a text input (const)
            html_code += f"""
            <small class="form-text text-muted">{parameter_name}:</small>
            <input type="text" class="form-control" disabled="disabled" name="{parameter_name}" value="{parameter_info['const']}">"""
        elif "list" in parameter_info:
            # Generate a dropdown (list)
            html_code += f"""
            <small class="form-text text-muted">{parameter_name}:</small>
            <select class="form-control" name="{parameter_name}">"""
            for option in parameter_info["list"]:
                html_code += f"""<option value="{option}">{option}</option>"""
            html_code += f"""</select>"""
        elif "check" in parameter_info:
            # Generate checkboxes (check)
            html_code += f"""
            <small class="form-text text-muted">{parameter_name}:</small>"""
            for option in parameter_info["check"]:
                html_code += f"""
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="{parameter_name}" value="{option}" id="{option}" checked>
                    <label class="form-check-label" for="{option}"><span class="grey-text">{option}</span></label>
                </div>

                """
        elif "field" in parameter_info:
            # Generate an input field (field)
            html_code += f"""
            <small class="form-text text-muted">{parameter_name}:</small>
            <input class="form-control" type="number" name="{parameter_name}" value="{parameter_info['field']}">"""
    return html_code


def __generate_arelight_log__(clean=False):
    if clean:
        open(SETTINGS["path_to_arelight_log"], "w").write("")
        return None
    html_code = ""
    for line in open(SETTINGS["path_to_arelight_log"], "r").readlines():
        html_code += "\n<p>" + line + "</p>"
    return html_code


def __set_data_status__(filename, data):
    data_status = json.load(open(data_status_file, "r"))
    data_status["data"][filename] = data
    json.dump(data_status, open(data_status_file, "w"))


def __get_data_status__(filename):
    return json.load(open(data_status_file, "r"))["data"][filename]


def __update_data_status__(filename, status):
    data = __get_data_status__(filename)
    data["data_status"] = status
    __set_data_status__(filename, data)


def get_all_data_status():
    return json.load(open(data_status_file, "r"))["data"]


def __get_html_template__():
    return open("template_v2.html", "r").read().replace("<!--ARELIGHT ARGUMENTS-->", generate_ARELIGHT_PARAMETERS())


def __get_html_template_busy__():
    return open("template_busy.html", "r").read().replace("<!-- INSERT ARELIGHT LOG -->", __generate_arelight_log__())


@app.route('/file_status', methods=['GET', 'POST'])
def get_file_status():
    file = request.args.get('file')
    if not file:
        return jsonify({'error': 'Key is missing'}), 400
    return jsonify({"data": __get_data_status__(file)})


@app.route('/available_files', methods=['GET', 'POST'])
def get_all_file_names():
    return jsonify(list(get_all_data_status().keys()))


@app.route('/get_force_data', methods=['GET', 'POST'])
def get_force_data():
    if request.method == 'POST':
        # Your existing POST method code
        if request.is_json:
            data = request.get_json()
            return jsonify({"graph": json.load(open(os.path.join(SETTINGS["path_to_force_data"], os.path.basename(data["file"])+".json"), "r"))})

    elif request.method == 'GET':
        # Code to handle GET request
        file_name = request.args.get('file')
        print(file_name)
        if file_name:
            try:
                # Attempt to open the specified file
                with open(os.path.join(SETTINGS["path_to_force_data"], os.path.basename(file_name)+".json"), "r") as file:
                    data = json.load(file)
                return jsonify(data)
            except FileNotFoundError:
                # File not found error handling
                return jsonify({"error": "File not found"}), 404

        # Default response
    return jsonify({"graph": {"nodes": {"id": "DATASET NOT EXIST", "c": 1}, "links": []}})


@app.route('/details', methods=['POST'])
def get_details():
    def filter_records(record, conditions):
        for c in conditions:
            counter = True
            for key in c:
                if c[key] != record[key]:
                    counter = False
                    break
            if counter:
                return True
        return False

    if request.is_json:
        data = request.get_json()
        links = data["links"]
        draw_parameters = data["draw_parameters"]
        basis = data["basis"]
        texts = []

        conditions = []
        for filename in basis:
            for l in links:
                conditions.append({
                    "s_type": l["source"]["id"].split(".")[0],
                    "s_val": l["source"]["id"].split(".")[1],
                    "t_type": l["target"]["id"].split(".")[0],
                    "t_val": l["target"]["id"].split(".")[1],
                    "label": l["sent"],
                    "filename": filename
                })

        data_it = AREkitSamplesService.iter_samples_and_predict_sqlite3(
            sqlite_filepath=join("/Users/kmax/PycharmProjects/ARElight-main/test/data", "samples_and_predict-test"),
            samples_table_name="contents",
            predict_table_name="open_nre_bert",
            filter_record_func=lambda record: filter_records(record, conditions))
        results = []
        for data in tqdm(data_it):
            if True:
                results += [data]
        print(results)

        return jsonify({"results": results})

    else:
        print("/details ERROR - request is not a json")


@app.route('/get_radial_data', methods=['GET', 'POST'])
def get_radial_data():
    if request.method == 'POST':
        # Your existing POST method code
        if request.is_json:
            data = request.get_json()
            return jsonify({"graph": json.load(open(os.path.join(SETTINGS["path_to_radial_data"], os.path.basename(data["file"])+".json"), "r"))})

    elif request.method == 'GET':
        # Code to handle GET request
        file_name = request.args.get('file')
        if file_name:
            try:
                # Attempt to open the specified file
                with open(os.path.join(SETTINGS["path_to_radial_data"], os.path.basename(file_name)+".json"), "r") as file:
                    data = json.load(file)
                return jsonify(data)
            except FileNotFoundError:
                # File not found error handling
                return jsonify({"error": "File not found"}), 404

        # Default response
    return jsonify([{"w": 0.5, "imports": [], "name": "DATASET NOT EXIST"}])


arelight_thread = Thread()
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global arelight_thread
    def is_process_running():
        return arelight_thread.is_alive()

    def run_arelight(filename, options):
        try:
            args = [f'--{key}={value}' for key, value in options.items() if key != 'status']
            for arg in SETTINGS["arelight_const_args"].keys():
                args += ["--" + arg + "=" + SETTINGS["arelight_const_args"][arg]]
            print("     RUNNING ARELIGHT")
            __generate_arelight_log__(clean=True)
            subprocess.run(['python3', '-m', SETTINGS["installed_arelight"], "--from-files", filename, "--log-file", SETTINGS["path_to_arelight_log"]] + args, check=True)
            __update_data_status__(filename, 'completed')
        except Exception as e:
            __update_data_status__(filename, f'error: {str(e)}')

    if not is_process_running():
        if request.method == 'POST':
            # CASE 1 - run arelight
            if 'file' in request.files:

                f = request.files['file']
                file_path = os.path.join(SETTINGS["path_to_raw_data"], f.filename)
                f.save(file_path)
                options = {key: "|".join(request.form.getlist(key)) if key == 'ner-types' else request.form.get(key)
                           for key in request.form.keys()}
                arelight_thread = Thread(target=run_arelight, args=(file_path, options))
                arelight_thread.start()
                __set_data_status__(file_path, options)
                return render_template_string(__get_html_template_busy__())

            # CASE 2 - when uploading names of datasets to perform graph operations
            elif request.is_json:
                data = request.get_json()
                print(data)

        return render_template_string(__get_html_template__())
    else:
        return render_template_string(__get_html_template_busy__())


if __name__ == '__main__':
    open(SETTINGS["path_to_arelight_log"], "w").write("")
    app.run(port=8080, debug=True)
