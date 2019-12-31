from lake.catalog.glue_manager import start as start_crawler


def crawler(json_input, context):
    start_crawler()
