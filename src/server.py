from flask import Flask, jsonify, request
from solver import schedule_jobs

app = Flask(__name__)


@app.route("/health")
def health():
    return {"healthy": True}


# try
# http POST localhost:5000/schedule data:='[[[0,3],[1,2],[2,2]],[[0,2],[2,1],[1,4]],[[1,4],[2,3]]]'
@app.post("/schedule")
def schedule():
    if request.json and isinstance(request.json.get("data"), list):
        jobs_data = request.json.get("data")
        return jsonify(schedule_jobs(jobs_data))

    return ("", 400)
