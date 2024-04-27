from typing import Any
from flask import Flask, jsonify, request
from jsonschema import Draft7Validator
from robot_cafe.solver import JobsData, TaskInput, schedule_jobs

jobs_data_schema = {
    "type": "array",
    "items": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "duration": {"type": "integer"},
                "machine": {"type": "integer"},
            },
        },
    },
}

schedule_endpoint_schema = {
    "type": "object",
    "properties": {"data": jobs_data_schema},
    "required": ["data"],
}

# TODO(IL, 2024-04-27): this should be a unit test
Draft7Validator.check_schema(schedule_endpoint_schema)

schedule_endpoint_validator = Draft7Validator(schedule_endpoint_schema)


app = Flask(__name__)


@app.route("/health")
def health():
    return {"healthy": True}


# try:
# http POST localhost:5000/schedule data:='[
#        [
#            {"machine": 0, "duration": 3},
#            {"machine": 1, "duration": 2},
#            {"machine": 2, "duration": 2}
#        ],
#        [
#            {"machine": 0, "duration": 2},
#            {"machine": 2, "duration": 1},
#            {"machine": 1, "duration": 4}
#        ],
#        [
#            {"machine": 1, "duration": 4},
#            {"machine": 2, "duration": 3}
#        ]]'
@app.post("/schedule")
def schedule():
    json_data = request.json
    if json_data is not None and schedule_endpoint_validator.is_valid(json_data):  # pyright: ignore[reportUnknownMemberType]
        jobs_data_json: list[list[dict[str, Any]]] = json_data.get("data")
        jobs_data: JobsData = [
            [
                TaskInput(duration=task["duration"], machine=task["machine"])
                for task in jobs
            ]
            for jobs in jobs_data_json
        ]
        return jsonify(schedule_jobs(jobs_data))

    return ("", 400)
