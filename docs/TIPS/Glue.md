# AWS Glue

- [AWS Glue](#aws-glue)
  - [はじめに](#はじめに)
  - [CLI](#cli)
    - [ジョブ削除](#ジョブ削除)
    - [ジョブ作成](#ジョブ作成)
    - [ジョブの取得](#ジョブの取得)
    - [ジョブの実行](#ジョブの実行)
  - [AWSコンソール画面からの操作](#awsコンソール画面からの操作)
    - [ジョブの作成](#ジョブの作成)
  - [Glue をローカルでデバッグする](#glue-をローカルでデバッグする)
    - [小さいテストデータの作り方](#小さいテストデータの作り方)
    - [ローカルで AWS 無しで開発する](#ローカルで-aws-無しで開発する)
    - [ローカルで LocalStack を使って開発する](#ローカルで-localstack-を使って開発する)
    - [ローカルで Glue を動かすけど AWS の実データを使ってテストする](#ローカルで-glue-を動かすけど-aws-の実データを使ってテストする)
      - [History Server](#history-server)
    - [ユニットテスト](#ユニットテスト)
      - [実装例](#実装例)
      - [ユニットテスト用のテストデータ](#ユニットテスト用のテストデータ)
      - [テスト実行](#テスト実行)
    - [性能テスト用のユニットテスト](#性能テスト用のユニットテスト)
      - [テストデータの作り方](#テストデータの作り方)
        - [aws cli のプロファイルを準備する](#aws-cli-のプロファイルを準備する)
        - [ローカルにテストデータ置き場を作る](#ローカルにテストデータ置き場を作る)
        - [性能テスト用データを作成する](#性能テスト用データを作成する)
        - [VMのメモリ設定を大きくする](#vmのメモリ設定を大きくする)
          - [Docker Desktop の場合](#docker-desktop-の場合)
          - [Docker Toolbox の場合](#docker-toolbox-の場合)
          - [Vagrant の場合](#vagrant-の場合)
        - [性能テスト実装例](#性能テスト実装例)
        - [性能テスト実行](#性能テスト実行)
  - [AWS 上の Glue でテストする](#aws-上の-glue-でテストする)
    - [実行エラー (Failed) のログの見方](#実行エラー-failed-のログの見方)
  - [TIPS](#tips)
    - [on_cw_event からの event の中身](#on_cw_event-からの-event-の中身)
    - [CSVの取込のオプション](#csvの取込のオプション)
    - [システム要件](#システム要件)
    - [executor数 とか メモリの設定](#executor数-とか-メモリの設定)
    - [並列度の性能調整](#並列度の性能調整)
    - [同時実行数の制限](#同時実行数の制限)
      - [制限を超えて起動したときの例外](#制限を超えて起動したときの例外)
    - [help](#help)
  - [参考記事](#参考記事)

## はじめに

**glueの動作イメージ**  
glue は、 **たぶん** 、こんな動作イメージです。  
サービスの実態としては Spark が動いています。 Spark に対して、スクリプトを送信して Spark 内でそのスクリプトが実行される・・・という動作イメージです。  
glue用のスクリプトをローカルの python インタープリターで実行するというのとはちょっと違います。  

**glue のスクリプトは S3 に配置される**  
glueのAWSコンソールでスクリプトを編集して、登録することもできるのだけど、編集したスクリプトは、S3に保存されます。  
そのため、そのS3のパスのスクリプトを上書きしたらOKなので、デプロイは、コピーで行う感じになります。

最初のglueのジョブ登録だけはコンソールから行う方法しか、わかっていないが、その登録時に、保存先のS3パスを設定しているので、そのパスにコピーします。

## CLI

参考：

- <https://docs.aws.amazon.com/cli/latest/reference/glue/index.html#cli-aws-glue>
- <https://docs.aws.amazon.com/ja_jp/glue/latest/dg/add-job-python.html>
- <https://docs.aws.amazon.com/glue/latest/webapi/API_CreateJob.html>
- <https://qiita.com/pioho07/items/aca43eb9d89ca9a0c52a>

```bash
# スケルトン出力
aws glue create-job --generate-cli-skeleton > job.json
```

スケルトンからのジョブ例

```json
{
    "Name": "test-rd_radiko_adid",
    "Role": "d-radiodots-glue-dev",
    "ExecutionProperty": {
        "MaxConcurrentRuns": 3
    },
    "Command": {
        "Name": "glueetl",
        "ScriptLocation": "s3://d-radiodots-data-stg/test/rd_radiko_adid.py",
        "PythonVersion": "3"
    },
    "DefaultArguments": {
        "--TempDir": "s3://d-radiodots-data-stg/aws-glue-temporary",
        "--extra-py-files": "s3://d-radiodots-data-stg/test/my-glue-lib.zip",
        "--job-bookmark-option": "job-bookmark-disable",
        "--job-language": "python"
    },
    "MaxRetries": 0,
    "Timeout": 2880,
    "MaxCapacity": 5.0,
    "GlueVersion": "1.0"
}
```

- **Command.Name** Sparkを使う場合は glueetl
- **MaxCapacity** 最大容量
- **ExecutionProperty.MaxConcurrentRuns** 最大同時実行数
- **DefaultArguments.--TempDir** 一時ディレクトリ（指定しないとエラーになる）
- **DefaultArguments.--extra-py-files** スクリプトが複数ファイルで構成されている場合は、zipにしてパスを指定する

### ジョブ削除

```bash
aws glue delete-job --job-name test-rd_radiko_adid
```

### ジョブ作成

先にスクリプトをS3に配置

```bash
LOCALDIR=/workspace/glue/src
S3DIR=s3://d-radiodots-data-dev/aws-glue-scripts/rd_radiko_adid

# スクリプトをコピー
aws s3 cp $LOCALDIR/rd_radiko_adid.py $S3DIR/rd_radiko_adid.py
# スクリプトが複数ファイルで構成されるので、extra-py-files 用に zipしてコピー
(cd $LOCALDIR && zip -r /tmp/my-glue-lib.zip . -x '*__pycache__*' '*.pytest_cache*')
aws s3 cp /tmp/my-glue-lib.zip $S3DIR/my-glue-lib.zip

```

ジョブの作成

```bash
aws glue create-job --cli-input-json file://job.json
```

### ジョブの取得

```bash
aws glue get-job --job-name import_ad_imp_dev
```

### ジョブの実行

```bash
#job_id=rd_radiko_adid
job_id=rd_radiko_reception
stg=dev
job_name="import_${job_id}_${stg}"

aws glue start-job-run \
  --job-name $job_name \
  --arguments '{"--JOB_NAME":"test","--DATE_PARAM":"2020-06-01","--BUCKET_NAME":"d-radiodots-data-dev","--STREAM_TYPE":"live"}'

```

再実行するときは、ジョブIDを指定する

```bash
aws glue start-job-run \
  --job-name import_rd_radiko_adid_dev \
  --job-run-id jr_c5dd3423edb2c74d624a809ee3709780d4c6515f2cb7641f5a34c27736ea5ab1

```

## AWSコンソール画面からの操作

### ジョブの作成

ジョブの作成手順です。

* AWSコンソールのGlueを開く
* サイドメニューの「ジョブ」 を選択
* 「ジョブの追加」ボタン押下
    * **名前**
      任意に名前をつける。ジョブ実行時の指定に使われる。
    * **IAMロール**
      選択する（無ければ作成）
    * **Type**
      Spark
    * **Glue Version**
      Spark 2.4 （Glue Version 1.0）
    * **このジョブ実行**
      ユーザーが作成する新しいスクリプト
    * **スクリプトファイル名**
      e.g.) example.py
    * **スクリプトが保存されている S3 パス**
        * (dev環境) s3://d-radiodots-data-dev/aws-glue-scripts
        * (stg環境) s3://d-radiodots-data-stg/aws-glue-scripts
        * (prod環境) s3://d-radiodots-data/aws-glue-scripts
    * **一時ディレクトリ**
        * (dev環境) s3://d-radiodots-data-dev/aws-glue-temporary
        * (stg環境) s3://d-radiodots-data-stg/aws-glue-temporary
        * (prod環境) s3://d-radiodots-data/aws-glue-temporary
    * **モニタリングオプション**
      * Spark UI
        * (dev環境) s3://d-radiodots-data-dev/aws-glue-eventlog
        * (stg環境) s3://d-radiodots-data-stg/aws-glue-eventlog
        * (prod環境) s3://d-radiodots-data/aws-glue-eventlog

    以上を設定して、「次へ」      

* 「接続」の画面では、何も追加しないで、「ジョブを保存してスクリプトを編集する」ボタン押下
* 「スクリプト編集」の画面では、何も書かずに、「保存」ボタンを押下

これで、ジョブだけ登録されたので、実際のスクリプトは、ローカルでデバッグしたものを、上記の S3パスとスクリプトファイル名 に上書きコピーしてデプロイします。

## Glue をローカルでデバッグする

dockerで実行できるようにしました。  
参考にしたのは、この2つの記事。  
<https://dev.classmethod.jp/articles/aws-glue-local/>  
<https://future-architect.github.io/articles/20191101/>  

作成した dockerイメージは、altus5/devcontainer-glue で公開してあります。（buildしなくて大丈夫）

docker-compose に glue というサービスで起動するようになっているので、次のようにコンテナに入って実行できます。

```bash
docker-compose exec glue bash
```

以降の説明は、特に指定がないものは、この glue コンテナの中で実行するものとします。

### 小さいテストデータの作り方

ローカルの開発では、小さいデータを用意して、サクサク開発した方がよいでしょう。

例えば、 2019/9/1 の gtlog のデータを小さくする場合を記します。  

```bash
## s3にあるデータを持ってくる
aws s3 cp s3://d-radiodots-data-dev/provision-data/from-d-stadia/radiko-gt/dt=2019-09-01/gt_radiko_v2_20190901-000.gz .
## デバッグ用なので100行に小さくする
gzip -dc log_reception_20200526000000.csv.gz | head -100 > log_reception_20200526000000-tail.csv
## ./db/fixture/srcdata/gtlog に移動
mkdir -p ./db/fixture/srcdata/gtlog
mv gt_radiko_v2_20190901-000 ./db/fixture/srcdata/gtlog
gzip ./db/fixture/srcdata/gtlog/gt_radiko_v2_20190901-000
```

### ローカルで AWS 無しで開発する

データをローカルにコピーしてきて Spark のロジックを手っ取り早く実装するのが最善です。  
ローカルのデータには、 `file://` スキーマで URL を指定すると Spark はローカルから読み出します。  
出力も同じくローカルに出力できます。そして、最初は、 parquet 形式ではなくて csv で出力して、出力された値を目で確認できた方がよいでしょう。  
いろいろ使い分けてデバッグしてみてください。

実装例  
※最新の実装では、複数のモジュールに分けて実装しているので、以下のような実装にはなっていません。

```python
import io
import sys
import csv
import logging
import datetime
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.sql import SQLContext
from pyspark.context import SparkContext
from pyspark.sql.types import StructType
from pyspark.sql.types import StructField
from pyspark.sql.types import StringType
from pyspark.sql.types import IntegerType
from pyspark.sql.types import BooleanType
from pyspark.sql.functions import *

# @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# ジョブ初期化
sc = SparkContext()
sqlContext = SQLContext(sc)
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
logger = glueContext.get_logger()

# ローカルのテストデータを読み込む
df = spark.read.csv(
    "file:///workspace/db/fixture/srcdata/gtlog/*.gz", header=True, sep=",")

# ・・・・
# ロジック
# ・・・・

# ローカルに保存する
(df
    .write
    .mode("overwrite")
    #.format("parquet")
    .format("com.databricks.spark.csv")
    .save("file:///workspace/.dstdata/gtlog/"))

# ジョブコミット
job.commit()
```

Glue にスクリプトを実行させる。  

```bash
env AWS_REGIION='ap-heaven-1' \
gluesparksubmit \
    ./glue/src/gtlog_conversion.py \
    --JOB_NAME='dummy'
```

### ローカルで LocalStack を使って開発する

LocalStackを使う方法は、なかなかうまく行かず、断念しています。  
やり方が分かり次第、書きます。  

### ローカルで Glue を動かすけど AWS の実データを使ってテストする

Glue(Spark)の実行は、ローカルで行うのだけど、元データは、S3上の実データを使いたい場合のやり方です。
実行するには、各自の credentials を環境変数に設定して、テストデータを配置して、 Glue を実行します。  

```bash
# cat /opt/.aws/credentials で見れます
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXX
export AWS_SECRET_ACCESS_KEY=YYYYYYYYYYY
export AWS_REGION=ap-northeast-1

# マスターデータ配置（prefcode.json）
aws s3 cp fixture/prefcode_master/prefcode.json s3://d-radiodots-data-dev/master-data/prefcode_master/

# テストデータ配置（コピーするデータは適宜自分で用意する）
# (e.g.) 2019/9/1のデータでデバッグする場合（担当者ごとにぶつからないようにしてください）
#
## s3に今あるデータが何か調べる
aws s3 ls d-radiodots-data-dev/provision-data/from-d-stadia/radiko-gt/
## s3にあるデータを持ってくる
aws s3 cp s3://d-radiodots-data-dev/provision-data/from-d-stadia/radiko-gt/dt=2019-09-01/gt_radiko_v2_20190901-000.gz .
## デバッグ用なので100行に小さくする
gzip -dc gt_radiko_v2_20190901-000.gz | head -100 > gt_radiko_v2_20190901-000
## 小さくしたデータをアップロードする
aws s3 cp data/small/gt_radiko_v2_20190901-000.gz s3://d-radiodots-data-dev/provision-data/from-d-stadia/radiko-gt/dt=2019-09-01/

# Glue 実行
## 方法1) スクリプトが1ファイルの場合
## ※上記のような1ファイルで実装している場合は、こちらの方法です。
gluesparksubmit \
    ./glue/src/rd_radiko_adid.py \
    --JOB_NAME='dummy' \
    --DATE_PARAM=2020-05-17 \
    --BUCKET_NAME='d-radiodots-data-stg' \
    --STREAM_TYPE=live
## 方法2) スクリプトが複数ファイルで構成される場合 py-files でzipにして指定する
## ※最新の実装では複数ファイルで実装しているのでzip化した方法を使ってください。
(cd $LOCALDIR && zip -r /tmp/my-glue-lib.zip . -x '*__pycache__*' '*.pytest_cache*')
gluesparksubmit \
    ./glue/src/rd_radiko_adid.py \
    --py-files /tmp/my-glue-lib.zip \
    --JOB_NAME='dummy' \
    --DATE_PARAM=2020-05-17 \
    --BUCKET_NAME='d-radiodots-data-stg' \
    --STREAM_TYPE=live

# 作成されたテーブルデータを見る
aws s3 ls d-radiodots-data-stg/test/listening-log/
```

#### History Server

Glueで実行されたジョブのDAGはDocker上のHistory Serverで確認することができます。
http://localhost:18081/ (Docker for * の場合)

History ServerでジョブをみるためにはAWS Glueのジョブ設定で`モニタリングオプションの以下の項目にチェックが必要です
* ジョブメトリクス
* 継続的なログ記録
* Spqrk UI
  * (dev環境) s3://d-radiodots-data-dev/aws-glue-eventlog
  * (stg環境) s3://d-radiodots-data-stg/aws-glue-eventlog
  * (prod環境) s3://d-radiodots-data/aws-glue-eventlog


### ユニットテスト

`glue/tests` にユニットテストが実装されています。

#### 実装例

glue/tests/lib/test_listening_log_df.py

```python
import pytest
import datetime
import pandas as pd

from lib import listening_log_df                                # (1)
from tests.lib.app_context_unit_mock import AppContextUnitMock  # (2)

def test_load(app_context):                                     # (3)
    result_df = listening_log_df.load(app_context)              # (4)
    df = result_df.toPandas()                                   # (5)

    # 作成された行数
    assert len(df.index) == 3
    # カラム名
    expected = set([
        'program_date', 'radiko_id', 'program_date_hour', 'program_count', 'user_key',
        'station_id', 'log_hour', 'log_day_of_week', 'listener_class', 'pref_id',
        'reception_start_unixtime', 'reception_end_unixtime', 'areafree_flg'])
    assert set(df.columns) == expected
    # program_date ・・・ パラメータで指定された放送日だけが取り込まれている
    assert set(df['program_date']) == set(['2020-05-17'])
    # radiko_id
    assert set(df['radiko_id']) == set(['uid001', 'uid002', 'uid003'])
```

補足説明

- (1) テストする本体
- (2) AppContextのユニットテスト用のモック（このシステム固有の実装です）
- (3) パラメータでテスト用のfixtureを受け取ります。  
    conftest.py で `@pytest.fixture` のデコレータがついた `app_context()` が実装されていますが、
    テスト関数の引数で、この関数名と同じパラメータ名を定義すると pytest が自動的にセットしてくれます。
- (4) 本体の実行
- (5) pandas の dataframe に変換  
    この本体関数の返り値は SparkのDataFrameを返しますが、テスト検証のところでは、
    扱いやすい pandas の dataframe に変換してます。  
    set() したもので assert で比較すると、楽にチェックできます。

#### ユニットテスト用のテストデータ

`db/fixture/unit/*` にあります。`AppContextUnitMock`の中で、テストデータを参照するように置き換えてます。

#### テスト実行

gluepytest でユニットテストを実行します。

例えば、`glue/tests/lib/test_listening_log_df.py`のテスト実行は、以下のように行います。

```bash
time gluepytest -s tests/lib/test_listening_log_df.py
```

### 性能テスト用のユニットテスト

実データを使ったテストは、1回の実行に、30分くらいかかってしまうので、
ローカルでの性能テストは、もう少し小さいデータで繰り返し実行したいので、
そのためのやり方です。

#### テストデータの作り方

小さいデータとは言え、ソースコードと一緒にコミットするには、大きすぎるので、
性能テスト用のテストデータは、実データを元に作成するところから始めます。

##### aws cli のプロファイルを準備する

1) profile=cm-radiko の名前で、radiko（クラメソ）のconfigとcredentialsを登録する
2) profile=fsi-lf の名前で、リスナーファインダー（FSI）のconfigとcredentialsを登録する

##### ローカルにテストデータ置き場を作る

`./data` ディレクトリにテストデータを作成します。  
※ `./data/.gitignore` を作成して、./data 配下がコミット対象にならないようにします。

```bash
LOCAL_ORG_DIR=./data/large
mkdir -p $LOCAL_ORG_DIR
LOCAL_SMALL_DIR=./data/small
mkdir -p $LOCAL_SMALL_DIR
LOCAL_MEDIUM_DIR=./data/medium
mkdir -p $LOCAL_MEDIUM_DIR
echo '*' > ./data/.gitignore
```

##### 性能テスト用データを作成する

聴取ログ(live)

```bash
SRCFILE=log_reception_20200517000000.csv.gz
SRCURI=s3://radiko-dashboard/radiko/log_reception_confirm/2020/05/17/$SRCFILE
aws s3 cp --profile cm-radiko $SRCURI $LOCAL_ORG_DIR/
# デバッグ用にデータを小さくする（100件）
gzip -dc $LOCAL_ORG_DIR/$SRCFILE | head -100 | gzip > $LOCAL_SMALL_DIR/$SRCFILE
# デバッグ用にデータを小さくする（2500万件）
gzip -dc $LOCAL_ORG_DIR/$SRCFILE | head -25000000 | gzip > $LOCAL_MEDIUM_DIR/$SRCFILE
```

聴取ログ(timefree)

```bash
SRCFILE=trs_reception_20200517000000.csv.gz
SRCURI=s3://radiko-dashboard/radiko/trs_reception/2020/05/17/$SRCFILE
aws s3 cp --profile cm-radiko $SRCURI $LOCAL_ORG_DIR/
# デバッグ用にデータを小さくする
gzip -dc $LOCAL_ORG_DIR/$SRCFILE | head -1000 | gzip > $LOCAL_SMALL_DIR/$SRCFILE
```

adidマスター

```bash
SRCFILE=map_radiko_ifa_20200517000000.csv.gz
SRCURI=s3://radiko-dashboard/radiko/map_radiko_ifa/2020/05/17/$SRCFILE
aws s3 cp --profile cm-radiko $SRCURI $LOCAL_ORG_DIR/
# デバッグ用にデータを小さくする（100件）
gzip -dc $LOCAL_ORG_DIR/$SRCFILE | head -100 | gzip > $LOCAL_SMALL_DIR/$SRCFILE
# デバッグ用にデータを小さくする（3千万件）
gzip -dc $LOCAL_ORG_DIR/$SRCFILE | head -30000000 | gzip > $LOCAL_MEDIUM_DIR/$SRCFILE
```

in_user

```bash
SRCFILE=backup_realtime_customer_20200517.csv.gz
SRCURI=s3://dexpf-radio/data-in/realtime/backup_user/onair_date=2020-05-17/$SRCFILE
aws s3 cp --profile fsi-lf $SRCURI $LOCAL_ORG_DIR/
# デバッグ用にデータを小さくする
gzip -dc $LOCAL_ORG_DIR/$SRCFILE | head -100 | gzip > $LOCAL_SMALL_DIR/$SRCFILE
```

people-imp

```bash
SRCFILE=log.csv.gz
SRCURI=s3://d-stadia/data-in/suppliers/105/export-logs/5/batch_date=2019-12-31/$SRCFILE
# assume-role で一時キーを取得する
aws sts assume-role --role-arn "arn:aws:iam::454152880029:role/ForRadioDotsUI" --role-session-name d-stadia-assume-role  --profile d-stadia
# 出力されたCredentialsを .aws/credentials の target1 にセットする
aws s3 cp --profile target1 $SRCURI $LOCAL_ORG_DIR/
# デバッグ用にデータを小さくする
gzip -dc $LOCAL_ORG_DIR/$SRCFILE | head -100000 | grep adimp | gzip > $LOCAL_SMALL_DIR/$SRCFILE
```

##### VMのメモリ設定を大きくする

###### Docker Desktop の場合

管理画面からメモリ設定を8Gに変更してください。

###### Docker Toolbox の場合

以下のコマンドで VMのメモリを大きくする

```bash
alias VBoxManage='/c/Program\ Files/Oracle/VirtualBox/VBoxManage.exe'

# 停止
docker-machine stop default
# vmの設定を変更 cpu=2 memory=8G
VBoxManage modifyvm "default" --cpus 2 --cpuexecutioncap 70 --memory 8192
# 開始
docker-machine start default
docker-machine env
```

###### Vagrant の場合

Vagrantfile の 以下を修正して reload してください

```diff
-   vb.memory = 4096
+   vb.memory = 8192
```

##### 性能テスト実装例

glue/tests/rd_radiko_adid_test.py

```python
import pytest
import os
import boto3
import datetime

from awsglue.job import Job

import rd_radiko_adid                           # (1)

@pytest.mark.skipif(                            # (2)
    os.environ.get('TEST_ENV', '') == '',
    reason="自動テストではテストデータがコミットされてないのでスキップ"
)
def test_convert_small(app_context_small):      # (3)
    ctx = app_context_small
    job = Job(ctx.glueContext)
    job.init('test', {})

    df = rd_radiko_adid.convert(ctx)            # (4)

    mock_write_df(ctx, df)                      # (5)
    job.commit()

def mock_write_df(ctx, df):
    (df
        # データがある程度大きい場合は、coalesce で1つにまとめない方がよい
        # .coalesce(1)
        .write
        #.partitionBy(["program_date", "station_id", 'listener_class'])
        .mode("overwrite")
        # parquet形式は出来上がりをエディタで見れないので
        # 最初のうちは csv で出力した方が無難
        .format("com.databricks.spark.csv").option("header", "true")
        #.format("parquet")
        # 
        # vagrantでマウントしたディレクトリだと
        # パーティショニングした xx=yy のディレクトリ名が問題になるので、
        # linux 内の /var/data/listening_log などに出力するのが無難で
        # cat /var/data/listening_log/* > a.out
        .save(ctx.output_listening_log_prefix)
        #.save("file:///workspace/.dstdata/")
        #.save(f"s3://d-radiodots-data-dev/test/nobita/")
    )
```

補足説明

- (1) テストする本体
- (2) テストスキップ  
    このテストケースの実装は、テストデータがコミットされてないので、
    自動テストではスキップされるように `@pytest.mark.skipif` で抑止しておくようにしてください。
    上記例は、 TEST_ENV=(small|medium|large) の環境変数がセットされているときのみ実行されるようになってます。
- (3) AppContext の性能テスト用モックのfixtureを受け取ります。  
    app_context_small は「[性能テスト用データを作成する](#性能テスト用データを作成する)」で作成してテストデータを参照するようになっている AppContext です。
- (4) 本体の実行
- (5) CSVに出力  
    テスト結果は、csv形式で実際の出力も行って、目視でも確認できるようにした方がよいでしょう。

##### 性能テスト実行

出力先を作成する。  
※vagrantなどで共有マウントされたディレクトリだと作成できないパスがあるので、コンテナ内のパスに作成する

```bash
export OUTDIR=/var/data/listening_log
mkdir -p $OUTDIR
```

実行する。

```bash
export TEST_ENV=small       # (注)
time gluepytest -s tests/rd_radiko_adid_test.py::test_convert_small
```

テストがスキップされないように環境変数をセットします。
time コマンドで実行時間を計測するとよいと思います。

CSVの出力結果を見る場合、`.coalesce(1)` しないと、複数のファイルに分割されているので、
出力結果を1つにまとめると、見やすくなります。

```bash
ls $OUTDIR

echo '' > result.csv
for file in $(find $OUTDIR -name '*.csv'); do
    cat $file >> result.csv
done
```

## AWS 上の Glue でテストする

ジョブを実行する（@see [ジョブの実行](#ジョブの実行)）

（例）

```bash
aws glue start-job-run \
  --job-name import_rd_radiko_adid_dev \
  --arguments '{"--JOB_NAME":"import_rd_radiko_adid_dev","--DATE_PARAM":"2020-04-01","--BUCKET_NAME":"d-radiodots-data-dev","--STREAM_TYPE":"live"}'

```

* AWSコンソールのGlueを開く
* サイドメニューの「ジョブ」 を選択
* ジョブの一覧から、該当するジョブを選択
* 「履歴」タブに実行結果が一覧表示されている
* 実行ステータスが Running の場合は、処理中である  
    Running でも、ログを見たときに CloudWatch でログが無いとエラーが表示されるときがあるが Glue を実行するインスタンスの起動の時間がかかっていて、ジョブが実行されてなくてログが作成されていない状態がある。
* 実行ステータスが Succeeded か Failed になるとジョブ終了である

### 実行エラー (Failed) のログの見方

実行ステータスが Failed になっている場合、エラーログのリンクをクリックすると、CloudWatchのログ画面に遷移します。

エラー時には、このログにあるスタックトレースをみて、原因を特定することになります。

よく見るスタックトレースとして、 `com.amazon.ws.emr.hadoop.fs.shaded.org.apache.http.conn.HttpHostConnectException: Connect to 0.0.0.0:8088 [/0.0.0.0] failed: Connection refused (Connection refused)` があります。  
もしも、これが WARN だった場合、このログは、無視してよいです。  
他にもスタックトレースがあると思うので、そっちが、本当のエラーです。

## TIPS

### on_cw_event からの event の中身

```json
{
    "version": "0",
    "id": "d837456d-e363-a31f-80ad-bffdc46fb324",
    "detail-type": "Glue Job State Change",
    "source": "aws.glue",
    "account": "373981184465",
    "time": "2020-10-31T21: 42: 35Z",
    "region": "ap-northeast-1",
    "resources": [],
    "detail": {
        "jobName": "import_ad_imp_prod",
        "severity": "INFO",
        "state": "SUCCEEDED",
        "jobRunId": "jr_e644fbaf2b95ae0dc9b0f4de78496c146158a15f11f6ad48f55880a0f0462772",
        "message": "Job run succeeded"
    }
}
```

### CSVの取込のオプション

セル内に改行のあるデータを取り込む場合は、 `.option('multiLine', 'true')` にする

※GTログではエスケープ方式が違っていて、これではダメだったが。

```python
data_frame = spark.read.option('multiLine', 'true').csv(
    f's3://{src_bucket_name}/{src_object_key_name}000.gz', header=True, sep="\t")
```

### システム要件

2020/4/29 時点

- aws-glue 1.0
- python 3.6
- spark 2.4.3
- java 1.8  
    sparkがこのバージョンじゃないとダメでした。
    標準のapt-getではリリースされてないので注意。

### executor数 とか メモリの設定

glue ではメモリとコア数の組み合わせを WorkerType で指定します。  
WorkerType は Glue のジョブ毎にコンソールから設定変更します。

選択可能な WorkerType

- Standard  
    --conf spark.executor.memory=5g  
    --conf spark.executor.cores=4  
- G.1X  
    --conf spark.executor.memory=10g  
    --conf spark.executor.cores=8  
- G2.X  
    --conf spark.executor.memory=20g  
    --conf spark.executor.cores=16  

### 並列度の性能調整

<https://qiita.com/blueskyarea/items/2e1b6317f8f10f6d3cbb>  
> 勘違い４．リソース（executor数、CPUコア数）を増やすだけで、並列度が増える

できるだけ均等に分散された方がよいので、データの特性に合わせて repartition して偏りを解消させてみる。

### 同時実行数の制限

事前にデータを作成するときに、まとめて、Glueを実行したいことがありますが、
同時実行には、制限があります。  
`1カウントで、同時に実行できるジョブは、最大50です`

https://dev.classmethod.jp/articles/aws-glue-job-concurrency/

#### 制限を超えて起動したときの例外

aws-glue は同時実行数の制限を超えて起動すると、ConcurrentRunsExceededException が返される。

### help

```bash
root@b9a2457fb567:/workspace# gluesparksubmit --help
Usage: spark-submit [options] <app jar | python file | R file> [app arguments]
Usage: spark-submit --kill [submission ID] --master [spark://...]
Usage: spark-submit --status [submission ID] --master [spark://...]
Usage: spark-submit run-example [options] example-class [example args]

Options:
  --master MASTER_URL         spark://host:port, mesos://host:port, yarn,
                              k8s://https://host:port, or local (Default: local[*]).
  --deploy-mode DEPLOY_MODE   Whether to launch the driver program locally ("client") or
                              on one of the worker machines inside the cluster ("cluster")
                              (Default: client).
  --class CLASS_NAME          Your application's main class (for Java / Scala apps).
  --name NAME                 A name of your application.
  --jars JARS                 Comma-separated list of jars to include on the driver
                              and executor classpaths.
  --packages                  Comma-separated list of maven coordinates of jars to include
                              on the driver and executor classpaths. Will search the local
                              maven repo, then maven central and any additional remote
                              repositories given by --repositories. The format for the
                              coordinates should be groupId:artifactId:version.
  --exclude-packages          Comma-separated list of groupId:artifactId, to exclude while
                              resolving the dependencies provided in --packages to avoid
                              dependency conflicts.
  --repositories              Comma-separated list of additional remote repositories to
                              search for the maven coordinates given with --packages.
  --py-files PY_FILES         Comma-separated list of .zip, .egg, or .py files to place
                              on the PYTHONPATH for Python apps.
  --files FILES               Comma-separated list of files to be placed in the working
                              directory of each executor. File paths of these files
                              in executors can be accessed via SparkFiles.get(fileName).

  --conf PROP=VALUE           Arbitrary Spark configuration property.
  --properties-file FILE      Path to a file from which to load extra properties. If not
                              specified, this will look for conf/spark-defaults.conf.

  --driver-memory MEM         Memory for driver (e.g. 1000M, 2G) (Default: 1024M).
  --driver-java-options       Extra Java options to pass to the driver.
  --driver-library-path       Extra library path entries to pass to the driver.
  --driver-class-path         Extra class path entries to pass to the driver. Note that
                              jars added with --jars are automatically included in the
                              classpath.

  --executor-memory MEM       Memory per executor (e.g. 1000M, 2G) (Default: 1G).

  --proxy-user NAME           User to impersonate when submitting the application.
                              This argument does not work with --principal / --keytab.

  --help, -h                  Show this help message and exit.
  --verbose, -v               Print additional debug output.
  --version,                  Print the version of current Spark.

 Cluster deploy mode only:
  --driver-cores NUM          Number of cores used by the driver, only in cluster mode
                              (Default: 1).

 Spark standalone or Mesos with cluster deploy mode only:
  --supervise                 If given, restarts the driver on failure.
  --kill SUBMISSION_ID        If given, kills the driver specified.
  --status SUBMISSION_ID      If given, requests the status of the driver specified.

 Spark standalone and Mesos only:
  --total-executor-cores NUM  Total cores for all executors.

 Spark standalone and YARN only:
  --executor-cores NUM        Number of cores per executor. (Default: 1 in YARN mode,
                              or all available cores on the worker in standalone mode)

 YARN-only:
  --queue QUEUE_NAME          The YARN queue to submit to (Default: "default").
  --num-executors NUM         Number of executors to launch (Default: 2).
                              If dynamic allocation is enabled, the initial number of
                              executors will be at least NUM.
  --archives ARCHIVES         Comma separated list of archives to be extracted into the
                              working directory of each executor.
  --principal PRINCIPAL       Principal to be used to login to KDC, while running on
                              secure HDFS.
  --keytab KEYTAB             The full path to the file that contains the keytab for the
                              principal specified above. This keytab will be copied to
                              the node running the Application Master via the Secure
                              Distributed Cache, for renewing the login tickets and the
                              delegation tokens periodically.

root@b9a2457fb567:/workspace#
```


## 参考記事

- [Glueの使い方的な](https://qiita.com/pioho07/items/32f76a16cbf49f9f712f)

