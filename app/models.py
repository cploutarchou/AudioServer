import datetime
import itertools
import json
import math
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import jsonify

from app import db


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def insert_entry(data: dict):
    required_fields = ['format_type', 'title', 'file_size', 'updated_at', 'status']
    results = None
    print(all(i.lower() in required_fields for i in data.keys()))
    if all(i.lower() in required_fields for i in data.keys()):
        data['created_at'] = datetime.now()
        print(data)
        results = db.Files.insert(data)

    return results


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def insert_batch(file: list = None):
    insetred_batches = []
    if 0 < len(file) < 5000:
        batches = {'created_at': datetime.now(), "updated_at": datetime.now(), "files": file}
        batch_id = db.Batches.insert(batches)
        insetred_batches.append(str(batch_id))
    else:
        ras = list(chunks(file, 5000))
        for i in ras:
            batches = {'created_at': datetime.now(), "updated_at": datetime.now(), "files": i}
            _id = db.Batches.insert(batches)
            insetred_batches.append(str(_id))
    return insetred_batches


def insert_upload(batches: list = None):
    batches = {'created_at': datetime.now(), "updated_at": datetime.now(), "batches": batches}
    batch_id = db.Uploads.insert(batches)
    return str(batch_id)


def get_upload_details(upload_id):
    uploads = db.Uploads
    batches = db.Batches
    files = db.Files
    res = uploads.find_one({"_id": ObjectId(upload_id)})

    data = []
    final_data = []
    if res and "batches" in res:
        for batch in res["batches"]:
            res = batches.find_one({"_id": ObjectId(batch)})
            if res and "files" in res:
                data.append(res["files"])
    data = list(itertools.chain(*data))
    for file in data:
        print("File")
        print(file)
        res = files.find_one({"_id": ObjectId(file)})
        print(res)
        if res:
            item = dict(objectid=file, file=f"{res['title']}.{res['format_type']}")
            final_data.append(item)

    return json.dumps(final_data, default=str)


def get_file(file_id):
    files = db.Files
    res = files.find_one({"_id": ObjectId(file_id)})
    res.pop("_id", None)
    if res and "file_size" in res:
        res['file_size'] = convert_size(res["file_size"])
        if res['status'] == 1:
            res['status'] = "active"
        else:
            print("else")
            res['status'] = "deleted"

    return json.dumps(res, default=str)


def get_top_10():
    from bson.json_util import dumps
    data = db.Files.aggregate([
        {"$group": {
            "_id": {
                "format_type": "$format_type"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.format_type": 1}},
        {"$group": {
            "_id": "$_id.format_type",
            "count": {"$mergeObjects": {"$arrayToObject": [[["$_id.format_type", "$count"]]]}}
        }},
        {"$limit": 1}])

    return dumps(list(data))


def get_average_file_size():
    data = db.Files.aggregate([
        {"$group": {"_id": "_id", "AverageValue": {"$avg": "$file_size"}}}
    ])
    list_cur = list(data)

    data = convert_size(int(list_cur[0]['AverageValue']))
    return {"AverageValue": data}


def last_7_days_upload():
    from bson.json_util import dumps
    files = db.Files
    week_before = datetime.now() - timedelta(days=6)
    data = files.aggregate([
        {
            '$match': {
                'created_at': {'$gt': week_before}
            },
        },
        {
            "$group": {
                "_id": {
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"},
                    "year": {"$year": "$created_at"}
                },
                "count": {"$sum": 1}
            }
        }

    ])
    data = json.loads(dumps(data))
    return jsonify(data)
