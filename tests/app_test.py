import sys

import pytest
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession

from src import app


@pytest.fixture(scope="module", autouse=True)
def glue_context() -> GlueContext:
    sys.argv.append("--JOB_NAME")
    sys.argv.append("test_job")

    args = getResolvedOptions(sys.argv, ["JOB_NAME"])
    sc = SparkSession.builder.getOrCreate()
    hc = sc._jsc.hadoopConfiguration()
    hc.set("fs.s3a.endpoint", "http://localstack:4566")
    hc.set("fs.s3a.path.style.access", "true")
    hc.set("fs.s3a.signing-algorithm", "S3SignerType")
    hc.set("fs.s3a.change.detection.mode", "None")
    hc.set("fs.s3a.change.detection.version.required", "false")
    context = GlueContext(sc)
    job = Job(context)
    job.init(args["JOB_NAME"], args)

    yield (context)

    job.commit()


def test_counts(glue_context: GlueContext) -> None:
    dyf = app.read_csv(glue_context, "s3://test-bucket/data/person.csv")
    dyf.printSchema()
    assert dyf.toDF().count() == 100


def test_execute_query(glue_context: GlueContext) -> None:
    dyf = app.read_csv(glue_context, "s3://test-bucket/data/person.csv")
    dyf.printSchema()
    df = app.execute_query(glue_context, dyf.toDF())
    df.show()
    df.printSchema()


def test_run(glue_context: GlueContext) -> None:
    dyf = app.read_csv(glue_context, "s3://test-bucket/data/person.csv")
    app.write_parquet(glue_context, dyf.toDF(), "s3://test-bucket/parquet")
