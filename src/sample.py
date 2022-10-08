import os
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession


class GluePythonSampleTest:
    def __init__(self):
        params = []
        if "--JOB_NAME" in sys.argv:
            params.append("JOB_NAME")
        args = getResolvedOptions(sys.argv, params)

        sc = SparkSession.builder.getOrCreate()
        self.context = GlueContext(sc)
        self.job = Job(self.context)

        s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
        if s3_endpoint_url:
            sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint", s3_endpoint_url)
            sc._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
            sc._jsc.hadoopConfiguration().set(
                "fs.s3a.signing-algorithm", "S3SignerType"
            )

        if "JOB_NAME" in args:
            jobname = args["JOB_NAME"]
        else:
            jobname = "test"
        self.job.init(jobname, args)

    def run(self):
        dyf = read_csv(
            self.context, "s3://test-bucket/examples/us-legislators/all/tokyo.csv"
        )
        dyf.printSchema()
        df = dyf.toDF()

        df = do_matching(self.context, df)
        df.show()
        write_parquet(df, "s3://test-bucket/output")

        self.job.commit()


def do_matching(glue_context, df):
    glue_context.get_logger().info("do_matching")
    df.createOrReplaceTempView("tokyo")
    df = glue_context.spark_session.sql(
        """
        SELECT
            *
        FROM
            tokyo
        ORDER BY
            listing_title_kana
        """
    )

    return df


def read_csv(glue_context, path):
    print(f"read_csv: {path}")
    dynamicframe = glue_context.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [path]},
        format="csv",
        format_options={"withHeader": True, "separator": ","},
    )
    return dynamicframe


def write_parquet(df, path):
    print(f"write_parquet: {path}")
    (
        df.write.mode("overwrite").format("parquet")
        # .partitionBy("var_1", "var_2")
        .save(path)
    )


if __name__ == "__main__":
    GluePythonSampleTest().run()
