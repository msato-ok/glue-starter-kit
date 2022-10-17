#!/bin/sh

S3_BUCKET=test-bucket
S3_URL=s3://$S3_BUCKET

# バケットの作成
awslocal s3 mb $S3_URL

# テストファイルを配置
DATA_DIR=/app/fixtures/it
awslocal s3 cp --recursive $DATA_DIR/ $S3_URL/data/
