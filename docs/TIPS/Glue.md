# AWS Glue

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
- [Glue 実行](#glue-実行)
  - [方法1) スクリプトが1ファイルの場合](#方法1-スクリプトが1ファイルの場合)
  - [方法2) スクリプトが複数ファイルで構成される場合 py-files でzipにして指定する](#方法2-スクリプトが複数ファイルで構成される場合-py-files-でzipにして指定する)
- [作成されたテーブルデータを見る](#作成されたテーブルデータを見る)
  - [実行エラー (Failed) のログの見方](#実行エラー-failed-のログの見方)
- [TIPS](#tips)
  - [on_cw_event からの event の中身](#on_cw_event-からの-event-の中身)
  - [CSVの取込のオプション](#csvの取込のオプション)
  - [システム要件](#システム要件)
  - [executor数 とか メモリの設定](#executor数-とか-メモリの設定)
  - [並列度の性能調整](#並列度の性能調整)
  - [同時実行数の制限](#同時実行数の制限)
    - [制限を超えて起動したときの例外](#制限を超えて起動したときの例外)
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
job_name=test_job
aws glue create-job --generate-cli-skeleton > job/${job_name}.json
```

スケルトンからのジョブ例

```json
{
    "Name": "test_job",
    "Role": "glue-dev-role",
    "ExecutionProperty": {
        "MaxConcurrentRuns": 3
    },
    "Command": {
        "Name": "glueetl",
        "ScriptLocation": "s3://test-bucket/glue/scripts/app.py",
        "PythonVersion": "3"
    },
    "DefaultArguments": {
        "--TempDir": "s3://test-bucket/glue/temp",
        "--extra-py-files": "s3://test-bucket/glue/scripts/lib.zip",
        "--job-bookmark-option": "job-bookmark-disable",
        "--job-language": "python"
    },
    "MaxRetries": 0,
    "Timeout": 2880,
    "MaxCapacity": 5.0,
    "GlueVersion": "3.0"
}
```

- **Command.Name** Sparkを使う場合は glueetl
- **MaxCapacity** 最大容量
- **ExecutionProperty.MaxConcurrentRuns** 最大同時実行数
- **DefaultArguments.--TempDir** 一時ディレクトリ（指定しないとエラーになる）
- **DefaultArguments.--extra-py-files** スクリプトが複数ファイルで構成されている場合は、zipにしてパスを指定する

### ジョブ削除

```bash
job_name=test_job

aws glue delete-job --job-name $job_name
```

### ジョブ作成

先にスクリプトをS3に配置

```bash
LOCALDIR=/app/src
S3DIR=s3://test-bucket/glue/scripts

# スクリプトをコピー
aws s3 cp $LOCALDIR/glue_starter_kit/app.py $S3DIR/app.py
# スクリプトが複数ファイルで構成されるので、extra-py-files 用に zipしてコピー
(cd $LOCALDIR && zip -r /tmp/lib.zip . -x '*__pycache__*' '*.pytest_cache*')
aws s3 cp /tmp/lib.zip $S3DIR/lib.zip

```

ジョブの作成

```bash
job_name=test_job

aws glue create-job --cli-input-json file://job/${job_name}.json
```

### ジョブの取得

```bash
job_name=test_job

aws glue get-job --job-name $job_name
```

### ジョブの実行

```bash
job_name=test_job

aws glue start-job-run \
  --job-name $job_name \
  --arguments '{"--JOB_NAME":"test","--PARAM1":"2020-06-01"}'

```

再実行するときは、ジョブIDを指定する

```bash
job_name=test_job

aws glue start-job-run \
  --job-name $job_name \
  --job-run-id jr_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

```

## AWSコンソール画面からの操作

### ジョブの作成

ジョブの作成手順です。

- AWSコンソールのGlueを開く
- サイドメニューの「ジョブ」 を選択
- 「ジョブの追加」ボタン押下
  - **名前**
      任意に名前をつける。ジョブ実行時の指定に使われる。
  - **IAMロール**
      選択する（無ければ作成）
  - **Type**
      Spark
  - **Glue Version**
      Spark 2.4 （Glue Version 1.0）
  - **このジョブ実行**
      ユーザーが作成する新しいスクリプト
  - **スクリプトファイル名**
      e.g.) example.py
  - **スクリプトが保存されている S3 パス**
    - s3://test-bucket/glue/scripts
  - **一時ディレクトリ**
    - s3://test-bucket/glue/temp
  - **モニタリングオプション**
    - Spark UI
      - s3://test-bucket/glue/logs

    以上を設定して、「次へ」

- 「接続」の画面では、何も追加しないで、「ジョブを保存してスクリプトを編集する」ボタン押下
- 「スクリプト編集」の画面では、何も書かずに、「保存」ボタンを押下

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
aws s3 cp s3://test-bucket/data/large.csv.gz .
## デバッグ用なので100行に小さくする
gzip -dc large.csv.gz | head -100 > test-data.csv
## ./fixtures/data に移動
mkdir -p ./fixtures/data
mv test-data.csv ./fixtures/data
gzip ./fixtures/data/test-data.csv
```

## Glue 実行

### 方法1) スクリプトが1ファイルの場合

※上記のような1ファイルで実装している場合は、こちらの方法です

gluesparksubmit \
    ./src/glue_starter_kit/app.py \
    --JOB_NAME='dummy' \
    --PARAM1=2020-05-17

### 方法2) スクリプトが複数ファイルで構成される場合 py-files でzipにして指定する

※最新の実装では複数ファイルで実装しているのでzip化した方法を使ってください

(cd $LOCALDIR && zip -r /tmp/lib.zip . -x '***pycache***' '*.pytest_cache*')
gluesparksubmit \
    ./src/glue_starter_kit/app.py \
    --py-files /tmp/lib.zip \
    --JOB_NAME='dummy' \
    --PARAM1=2020-05-17

## 作成されたテーブルデータを見る

aws s3 ls s3://test-bucket/parquet/

```bash

#### History Server

Glueで実行されたジョブのDAGはDocker上のHistory Serverで確認することができます。
http://localhost:18080/ (Docker for * の場合)

History ServerでジョブをみるためにはAWS Glueのジョブ設定で`モニタリングオプションの以下の項目にチェックが必要です
* ジョブメトリクス
* 継続的なログ記録
* Spqrk UI
  * s3://test-bucket/glue/logs


### ユニットテスト

`tests` にユニットテストが実装されています。


## AWS 上の Glue でテストする

ジョブを実行する（@see [ジョブの実行](#ジョブの実行)）

（例）

```bash
aws glue start-job-run \
  --job-name test_job \
  --arguments '{"--JOB_NAME":"test_job","--PARAM1":"2020-04-01"}'

```

- AWSコンソールのGlueを開く
- サイドメニューの「ジョブ」 を選択
- ジョブの一覧から、該当するジョブを選択
- 「履歴」タブに実行結果が一覧表示されている
- 実行ステータスが Running の場合は、処理中である  
    Running でも、ログを見たときに CloudWatch でログが無いとエラーが表示されるときがあるが Glue を実行するインスタンスの起動の時間がかかっていて、ジョブが実行されてなくてログが作成されていない状態がある。
- 実行ステータスが Succeeded か Failed になるとジョブ終了である

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
        "jobName": "test_job",
        "severity": "INFO",
        "state": "SUCCEEDED",
        "jobRunId": "jr_e644fbaf2b95ae0dc9b0f4de78496c146158a15f11f6ad48f55880a0f0462772",
        "message": "Job run succeeded"
    }
}
```

### CSVの取込のオプション

セル内に改行のあるデータを取り込む場合は、 `.option('multiLine', 'true')` にする

```python
data_frame = spark.read.option('multiLine', 'true').csv(
    f's3://{bucket_name}/{object_key_name}.csv.gz', header=True, sep="\t")
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

<https://dev.classmethod.jp/articles/aws-glue-job-concurrency/>

#### 制限を超えて起動したときの例外

aws-glue は同時実行数の制限を超えて起動すると、ConcurrentRunsExceededException が返される。

## 参考記事

- [Glueの使い方的な](https://qiita.com/pioho07/items/32f76a16cbf49f9f712f)
