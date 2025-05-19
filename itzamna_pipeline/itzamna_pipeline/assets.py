from dagster import asset

@asset
def hello():
    return "Hello, world!"
