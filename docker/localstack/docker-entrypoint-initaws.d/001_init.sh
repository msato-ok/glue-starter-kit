#!/bin/sh

S3_BUCKET=test-bucket
S3_URL=s3://$S3_BUCKET

# バケットの作成
awslocal s3 mb $S3_URL

# テストファイルを配置
DATA_DIR=/docker-entrypoint-initaws.d
awslocal s3 cp $DATA_DIR/tokyo.csv $S3_URL/examples/us-legislators/all/
