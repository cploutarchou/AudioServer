import datetime
import itertools
import json
import time
from datetime import datetime
from bson.objectid import ObjectId
from app import db


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
