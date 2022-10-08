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

        self.context = GlueContext(SparkSession.builder.getOrCreate())
        self.job = Job(self.context)

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
        write_parquet(self.context, dyf, "s3://test-bucket/output")

        self.job.commit()


def read_csv(glue_context, path):
    print(f"read_csv: {path}")
    dynamicframe = glue_context.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [path]},
        format="csv",
        format_options={"withHeader": False, "separator": ","},
    )
    return dynamicframe


def write_parquet(glue_context, inputDyf, path):
    print(f"write_parquet: {path}")
    (
        inputDyf.toDF()
        .write.mode("overwrite")
        .format("parquet")
        # .partitionBy("var_1", "var_2")
        .save(path)
    )

    # outputDF = glue_context.write_dynamic_frame.from_options(
    #     frame = inputDyf,
    #     connection_type = "s3",
    #     connection_options = {"path": path},
    #     format = "parquet"
    # )
    # return outputDF


if __name__ == "__main__":
    GluePythonSampleTest().run()
