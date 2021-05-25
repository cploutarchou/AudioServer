import datetime
import itertools
import json
import math
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from mongoengine import ListField, StringField, DateTimeField, Document, IntField, errors

from logger import logger
from main import db


class Files(Document):
    created_at = DateTimeField(required=True, index=True)
    file_size = IntField(required=True, index=True)
    format_type = StringField(required=True, index=True)
    updated_at = DateTimeField(required=True, index=False)
    status = IntField(default=1, index=True)
    title = StringField(required=True, index=True)
    meta = {
        "auto_create_index": True,
        "index_background": True,
        "indexes": [
            "created_at",
            "file_size",
            "format_type",
            "updated_at",
            "status",
            "title",
        ]
    }


class Batches(Document):
    created_at = DateTimeField(required=True, index=True)
    files = ListField(required=True)
    updated_at = DateTimeField(required=True, index=False)
    meta = {
        "auto_create_index": True,
        "index_background": True,
        "indexes": [
            "created_at",
            "updated_at"
        ]
    }


class Uploads(Document):
    batches = ListField(required=True)
    created_at = DateTimeField(required=True, index=True)
    updated_at = DateTimeField(required=True, index=False)
    meta = {
        "auto_create_index": True,
        "index_background": True,
        "indexes": [
            "created_at",
            "updated_at"
        ]
    }


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
    if all(i.lower() in required_fields for i in data.keys()):
        data['created_at'] = datetime.now()
        try:
            results = Files(
                created_at=data['created_at'], file_size=data['file_size'],
                format_type=data['format_type'], title=data['title'],
                updated_at=data['updated_at'], status=data['status'],
            ).save()
            results = results.id

        except errors.SaveConditionError as e:
            logger.error(f"Unable to save entry to db . Error {e}")

    return results


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def insert_batch(file: list = None):
    insetred_batches = []
    if 0 < len(file) < 5000:
        batch_id = Batches(created_at=datetime.now(), updated_at=datetime.now(), files=file).save()
        insetred_batches.append(str(batch_id.id))
    else:
        ras = list(chunks(file, 5000))
        for i in ras:
            _id = Batches(created_at=datetime.now(), updated_at=datetime.now(), files=i).save()
            insetred_batches.append(str(_id.id))
    print(insetred_batches)
    return insetred_batches


def insert_upload(batches: list = None):
    batch_id = Uploads(created_at=datetime.now(), updated_at=datetime.now(), batches=batches).save()
    return str(batch_id.id)


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
            res['status'] = "deleted"

    return json.dumps(res, default=str)


def get_top_10():
    pipeline = [
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
        {"$limit": 10}]

    data = Files.objects().aggregate(pipeline=pipeline)

    final_data = {}
    for i in data:
        final_data[i['_id']] = i['count'][i['_id']]
    sorted_items = {k: v for k, v in sorted(final_data.items(), key=lambda item: item[1], reverse=True)}
    return sorted_items


def get_average_file_size():
    data = Files.objects.average('file_size')
    data = convert_size(int(data))
    return {"AverageValue": data}


def last_7_days_upload():
    from bson.json_util import dumps
    week_before = datetime.now() - timedelta(days=6)

    # '$match': {"$or": [
    #     {'created_at': {'$gt': week_before}},
    #     {'updated_at': {'$gt': week_before}
    #      }]},
    data = Files.objects().aggregate([
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
                "items": {"$sum": 1}
            }
        }

    ])
    df_data = []
    data = json.loads(dumps(data))
    for i in range(len(data)):
        dat = data[i]
        df_data.append(
            dict(date=f"{dat['_id']['day']}-{dat['_id']['month']}-{dat['_id']['year']}", items=data[i]['items']))

    return dict(data=df_data)
