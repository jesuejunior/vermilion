from collections import defaultdict
from typing import Dict, List, Set

import boto3

from lake.config import settings

glue = boto3.client("glue")
s3 = boto3.client("s3")


class GlueManager:
    pass


DATABASES: Set = set()


def _check_db_exists(name):
    print("DBS: ", DATABASES)
    if name not in DATABASES:
        response = glue.get_databases()
        DATABASES.update({x["Name"] for x in response["DatabaseList"]})
        return name in DATABASES
        # response['ResponseMetadata']['HTTPStatusCode'] == 200
    return True


def _create_database(name: str):
    if not _check_db_exists(name):
        print(f"Creating database: {name}")
        response = glue.create_database(
            DatabaseInput={
                "Name": name,
                "Description": "Created automatically with Vermilion Lake",
                "LocationUri": f"S3://{settings.BUCKET}/{name}",
            }
        )
        print(f"Database created: {response}")
    return True


def _check_crawler_exists(name):
    try:
        response = glue.get_crawler(Name=name)
        if response.get("Crawler"):
            assert response.get("Crawler", {}).get("Name") == name
            return True
    except Exception as ex:
        print(ex)
        return False


def _start_crawler(name: str):
    response = glue.start_crawler(Name=name)
    print(response)
    return True


def _create_crawler(db: str, tables: List) -> bool:
    """
        Role "arn:aws:iam::12345678998876:role/service-role/AWSGlueServiceRole-Crawler",
    """
    name = f"{db}_crawler_{settings.NAMESPACE}"
    if not _check_crawler_exists(name):
        response = glue.create_crawler(
            Name=name,
            Role=settings.CRAWLER_ROLE,
            DatabaseName=db,
            Targets={"S3Targets": [{"Path": f"s3://{settings.BUCKET}/{db}/{table_name}"} for table_name in tables]},
            Schedule="cron(0 8 * * ? *)",
            SchemaChangePolicy={"UpdateBehavior": "UPDATE_IN_DATABASE", "DeleteBehavior": "DEPRECATE_IN_DATABASE"},
        )
    print(f"Starting {name}")
    _start_crawler(name)
    return True


def _get_data_from_s3():
    items: Dict = defaultdict(set)
    bucket: str = settings.BUCKET
    resp = s3.list_objects(Bucket=bucket, Prefix="", Delimiter="/")

    for folder in [x["Prefix"] for x in resp["CommonPrefixes"]]:
        resp = s3.list_objects(Bucket=bucket, Prefix=folder, Delimiter="/")
        for path in resp["CommonPrefixes"]:
            result = path["Prefix"].split("/")
            print(result)
            items[result[0]].add(result[1])

    return items


def main():
    print("Starting...")
    items = _get_data_from_s3()
    for db, tables in items.items():
        print(f"Creating database: {db} ")
        _create_database(db)
        print(f"Creating tables: {tables}")
        _create_crawler(db, tables)
