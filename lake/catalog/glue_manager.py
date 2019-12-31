from collections import defaultdict
from typing import Dict
import boto3
from config import settings

glue = boto3.client("glue")
s3 = boto3.client("s3")


class GlueManager:
    pass


DATABASES = set()


def _check_db_exists(name):
    print("DBS: ", DATABASES)
    if name not in DATABASES:
        response = glue.get_databases()
        DATABASES.update({x["Name"] for x in response["DatabaseList"]})
        return name in DATABASES
        # response['ResponseMetadata']['HTTPStatusCode'] == 200
    return True


def _create_database(name):
    if not _check_db_exists(name):
        print("Creating database: ", name)
        response = glue.create_database(
            DatabaseInput={
                "Name": name,
                "Description": "Created automatically with Vermilion Lake",
                "LocationUri": f"S3://{settings.BUCKET}/{name}",
            }
        )
        print("Database created: ", response)
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


def _start_crawler(name):
    response = glue.start_crawler(Name=name)
    print(response)
    return True


def _create_crawler(db, table_name):
    """
        Role "arn:aws:iam::12345678998876:role/service-role/AWSGlueServiceRole-Crawler",
    """
    name = f"{db}_{table_name}_crawler"
    if not _check_crawler_exists(name):
        response = glue.create_crawler(
            Name=name,
            Role=setting.CRAWLER_ROLE,
            DatabaseName=db,
            Targets={"S3Targets": [{"Path": f"s3://{settings.BUCKET}/{db}/{table_name}"}]},
            Schedule="cron(0 21 * * ? *)",
            SchemaChangePolicy={"UpdateBehavior": "UPDATE_IN_DATABASE", "DeleteBehavior": "DEPRECATE_IN_DATABASE"},
        )
    print("Starting {}".format(name))
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
        print("db: ", db)
        _create_database(db)
        for table_name in tables:
            print(table_name)
            _create_crawler(db, table_name)


if __name__ == "__main__":
    main()
