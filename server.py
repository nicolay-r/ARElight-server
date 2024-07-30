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

data_status_file = 'data_status.json'

SETTINGS = {
    "installed_arelight": "arelight.run.infer",
    "installed_operations": "arelight.run.operations",
    "path_to_raw_data": join(cur_dir, r"raw_data"),
    "path_to_arelight_log": join(cur_dir, r"arelight.log"),
    "path_to_force_data": join(cur_dir, r"output", r"force"),
    "path_to_radial_data": join(cur_dir, r"output", r"radial"),
    "path_to_sql_data": join(cur_dir, r"output"),
    "arelight_const_args": {
        "sampling-framework": "arekit"
    },
    "arelight_args": {
        "ner-model-name": {"list": ["ner_ontonotes_bert_mult"]},
        "ner-types": {"check": ["ORG", "PERSON", "LOC", "GPE"]},
        "terms-per-context": {"field": 50},
        "sentence-parser": {"list": ["nltk:russian"]},
        "text-b-type": {"list": ["nli_m"]},
        "tokens-per-context": {"field": 128},
        "bert-framework": {"list": ["opennre"]},
        "translate-framework": {"list": ["googletrans"]},
        "translate-text": {"list": ["en:ru"]},
        "batch-size": {"field": 10},
        "stemmer": {"list": ["mystem"]},
        "inference-writer": {"list": ["sqlite3"]},
        "pretrained-bert": {"list": ["DeepPavlov/rubert-base-cased"]},
        "bert-torch-checkpoint": {"list": ["ra4-rsr1_DeepPavlov-rubert-base-cased_cls.pth.tar"]},
        "backend": {"list": ["d3js_graphs"]}
    },
    "OP_UNION" : "UNION",
    "OP_INTERSECTION": "INTERSECTION",
    "OP_DIFFERENCE": "DIFFERENCE",
    "port": json.load(open(data_status_file, "r"))["server"]["port"]
}



# app = Flask(__name__)
app = Flask("ARElight-main")
CORS(app)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)


def __clean_filename__(filename):
    return filename.replace(".txt", "").replace(".json", "").replace(".csv", "").replace(" ","")

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
    filename = os.path.basename(filename)
    data_status = json.load(open(data_status_file, "r"))
    data_status["data"][filename] = data
    json.dump(data_status, open(data_status_file, "w"))


def __get_data_status__(filename):
    filename = os.path.basename(filename)
    return json.load(open(data_status_file, "r"))["data"][filename]


def __update_data_status__(filename, status):
    filename = os.path.basename(filename)
    data = __get_data_status__(filename)
    data["data_status"] = status
    __set_data_status__(filename, data)


def get_all_data_status():
    return json.load(open(data_status_file, "r"))["data"]


def __get_html_template__():
    return (open("template_v2.html", "r").read()
            .replace("<!--ARELIGHT ARGUMENTS-->", generate_ARELIGHT_PARAMETERS())
            .replace("<---SERVER-PORT--->", str(SETTINGS["port"]))
    )


def __get_html_template_busy__():
    return (open("template_busy.html", "r").read()
            .replace("<!-- INSERT ARELIGHT LOG -->", __generate_arelight_log__())
            .replace("<---SERVER-PORT--->", str(SETTINGS["port"]))
        )



@app.route('/file_status', methods=['GET', 'POST'])
def get_file_status():
    file = request.args.get('file')
    if not file:
        return jsonify({'error': 'Key is missing'}), 400
    return jsonify({"data": __get_data_status__(file)})


@app.route('/available_files', methods=['GET', 'POST'])
def get_all_file_names():
    return jsonify(list(map(lambda v: os.path.basename(v), get_all_data_status().keys())))


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

        print(record['s_val'], record["t_val"], record["label"])

        # print("***")
        for c in conditions:
            # print(c)
            counter = True
            for key in c:
                if key == 'filename':
                    record[key] = os.path.basename(record[key])
                if c[key] != record[key]:
                    counter = False
                    break
            if counter:
                # print("YES")
                return True
        # print("NOT FOUND")
        return False

    if request.is_json:
        data = request.get_json()
        links = data["links"]
        draw_parameters = data["draw_parameters"]
        basis = data["basis"]
        texts = []

        results = []
        for filename in basis:
            conditions = []
            for l in links:
                conditions.append({
                    "s_type": l["source"]["id"].split(".")[0],
                    "s_val": l["source"]["id"].split(".")[1],
                    "t_type": l["target"]["id"].split(".")[0],
                    "t_val": l["target"]["id"].split(".")[1],
                    "label": l["sent"],
                    "filename": filename
                })
            for c in conditions:
                print(c)

            print("connecting to ", join(SETTINGS["path_to_sql_data"], filename+"-test.sqlite"))

            data_it = AREkitSamplesService.iter_samples_and_predict_sqlite3(
                sqlite_filepath=join(SETTINGS["path_to_sql_data"], filename+"-test"),
                samples_table_name="contents",
                predict_table_name="open_nre_bert",
                filter_record_func=lambda record: filter_records(record, conditions))

            for data in tqdm(data_it):
                if True:
                    print(data)
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
            print(['python3', '-m', SETTINGS["installed_arelight"], "--from-files", filename, "--log-file", SETTINGS["path_to_arelight_log"]] + args)
            subprocess.run(['python3', '-m', SETTINGS["installed_arelight"], "--from-files", filename, "--log-file", SETTINGS["path_to_arelight_log"]] + args, check=True)
            __update_data_status__(filename, 'completed')
        except Exception as e:
            __update_data_status__(filename, f'error: {str(e)}')

    def run_operation(A, B, operation, new_dataset_name):
        try:
            print("     RUNNING OPERATION")
            __generate_arelight_log__(clean=True)
            command = ['python3', '-m', SETTINGS["installed_operations"],
                       "--weights", "y",
                       "-o", SETTINGS["path_to_sql_data"],
                       "--operation", operation,
                       "--graph_a_file", A,
                       "--graph_b_file", B,
                       "--name", new_dataset_name,
                       "--description", A+"___"+operation+"___"+B
                   ]
            print(command)
            subprocess.run(command, check=True)
        except Exception as e:
            print(f'error: {str(e)}')


    if not is_process_running():

        # if request.method == 'GET':
        #     print("hihihi")
        #     obj = request.args.to_dict()
        #     if 'operation' in obj:
        #         print(obj['operation'].keys())

        if request.method == 'POST':

            # CASE 1 - run arelight
            if 'file' in request.files:
                f = request.files['file']
                file_path = os.path.join(SETTINGS["path_to_raw_data"], __clean_filename__(f.filename))
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
                if 'operation' in data and len(data['operation']["A"])>0 and len(data['operation']["B"])>0:
                    A_files = list(map(lambda f: __clean_filename__(os.path.basename(f))+".json",data['operation']["A"]))
                    B_files = list(map(lambda f: __clean_filename__(os.path.basename(f))+".json",data['operation']["B"]))
                    operation = data['operation']["O"]
                    new_dataset_name = "[OPERATION]"+(data['operation']["D"].replace(" ","").replace("[OPERATION]","").replace(".json", ""))

                    if data['operation']["D"] == "":
                        new_dataset_name = (
                                            "[OPERATION]"+
                                            __clean_filename__("+".join(A_files))+
                                            "___"+operation+"___"+
                                            __clean_filename__("+".join(B_files))
                        )

                    temporary_A = os.path.join(SETTINGS["path_to_force_data"], "[OPERATION]temporary_A.json")
                    if len(A_files) > 1:
                        for idx, file in enumerate(A_files):
                            file = os.path.join(SETTINGS["path_to_force_data"], file)
                            if idx == 1:
                                run_operation(A_files[0], A_files[1], SETTINGS["OP_UNION"], "temporary_A")
                            if idx > 1:
                                run_operation(temporary_A, file, SETTINGS["OP_UNION"], "temporary_A")
                    else:
                        temporary_A = os.path.join(SETTINGS["path_to_force_data"], A_files[0])

                    temporary_B = os.path.join(SETTINGS["path_to_force_data"], "[OPERATION]temporary_B.json")
                    if len(B_files) > 1:
                        for idx, file in enumerate(B_files):
                            file = os.path.join(SETTINGS["path_to_force_data"], file)
                            if idx == 1:
                                run_operation(B_files[0], B_files[1], SETTINGS["OP_UNION"], "temporary_B")
                            if idx > 1:
                                run_operation(temporary_B, file, SETTINGS["OP_UNION"], "temporary_B")
                    else:
                        temporary_B = os.path.join(SETTINGS["path_to_force_data"], B_files[0])

                    run_operation(temporary_A, temporary_B, operation, new_dataset_name)

                    __set_data_status__(new_dataset_name, {"new dataset":"generated from operation"})
                return render_template_string(__get_html_template_busy__())



        return render_template_string(__get_html_template__())
    else:
        return render_template_string(__get_html_template_busy__())


if __name__ == '__main__':
    open(SETTINGS["path_to_arelight_log"], "w").write("")
    app.run(port=SETTINGS["port"], debug=True)
