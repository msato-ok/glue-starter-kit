import logging
import os
import sys

from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import DataFrame, SparkSession

logger = logging.getLogger(__name__)


class GluePythonSample:
    def __init__(self) -> None:
        params = []
        if "--JOB_NAME" in sys.argv:
            params.append("JOB_NAME")
        args = getResolvedOptions(sys.argv, params)

        sc = SparkSession.builder.getOrCreate()
        self.context = GlueContext(SparkContext.getOrCreate())
        self.job = Job(self.context)

        s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
        if s3_endpoint_url:
            hc = sc._jsc.hadoopConfiguration()
            hc.set("fs.s3a.endpoint", s3_endpoint_url)
            hc.set("fs.s3a.path.style.access", "true")
            hc.set("fs.s3a.signing-algorithm", "S3SignerType")

        if "JOB_NAME" in args:
            jobname = args["JOB_NAME"]
        else:
            jobname = "test"

        self.job.init(jobname, args)

    def run(self) -> None:
        dyf = read_csv(self.context, "s3://test-bucket/data/person.csv")
        df = execute_query(self.context, dyf.toDF())
        write_parquet(self.context, df, "s3://test-bucket/parquet44")

        self.job.commit()


def read_csv(glue_context: GlueContext, path: str) -> DynamicFrame:
    dynamicframe = glue_context.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [path]},
        format="csv",
        format_options={
            "withHeader": True,
            # "optimizePerformance": True,
        },
    )
    return dynamicframe


def write_parquet(glue_context: GlueContext, df: DataFrame, path: str) -> None:
    print(f"write_parquet: {path}")
    # df = df.coalesce(1)
    (
        df.write.mode("overwrite").format("parquet")
        # .partitionBy("gender")
        .save(path)
    )


def execute_query(glue_context: GlueContext, df: DataFrame) -> DataFrame:
    glue_context.get_logger().info("execute_query")
    df.createOrReplaceTempView("person")
    df = glue_context.spark_session.sql(
        """
        SELECT
            *
        FROM
            person
        """
    )

    return df


if __name__ == "__main__":
    GluePythonSample().run()
