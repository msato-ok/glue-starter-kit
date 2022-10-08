import sys

import pytest
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession

from src import sample


@pytest.fixture(scope="module", autouse=True)
def glue_context():
    sys.argv.append("--JOB_NAME")
    sys.argv.append("test_job")

    args = getResolvedOptions(sys.argv, ["JOB_NAME"])
    sc = SparkSession.builder.getOrCreate()
    sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://localstack:4566")
    sc._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
    sc._jsc.hadoopConfiguration().set("fs.s3a.signing-algorithm", "S3SignerType")
    sc._jsc.hadoopConfiguration().set("fs.s3a.change.detection.mode", "None")
    sc._jsc.hadoopConfiguration().set(
        "fs.s3a.change.detection.version.required", "false"
    )
    context = GlueContext(sc)
    job = Job(context)
    job.init(args["JOB_NAME"], args)

    yield (context)

    job.commit()


def test_counts(glue_context):
    dyf = sample.read_csv(
        glue_context, "s3://test-bucket/examples/us-legislators/all/tokyo.csv"
    )
    dyf.printSchema()
    assert dyf.toDF().count() == 10000


def test_do_matching(glue_context):
    dyf = sample.read_csv(
        glue_context, "s3://test-bucket/examples/us-legislators/all/tokyo.csv"
    )
    dyf.printSchema()
    df = sample.do_matching(glue_context, dyf.toDF())
    df.show()
    df.printSchema()


def test_run(glue_context):
    dyf = sample.read_csv(
        glue_context, "s3://test-bucket/examples/us-legislators/all/tokyo.csv"
    )
    sample.write_parquet(dyf.toDF(), "s3://test-bucket/examples/parquet")
    # sample.write_parquet(glue_context, dyf, "file:///home/glue_user/workspace/data")
