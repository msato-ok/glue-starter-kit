# glue-starter-kit

AWS Glue ジョブをローカルで開発するスターターキット

## Docker コンテナの構成

- app
  - このコンテナは VSCode 用のリモートコンテナで、テスト以外のコード編集や linting を行うことを目的としています。
  - awslocal コマンドをインストール済みなので、localstack を操作する場合は、 aws コマンドの代わりに awslocal を使ってください。
- glue
  - AWS 製の Glue コンテナです。テストを行うためのコンテナです。
  - SparkUI は <http://localhost:4040/>
  - Spark History Server は <http://localhost:18080/>
- localstack
  - S3 のエミュレータ。

※ glue コンテナの UID が 10000 になっていて、ホスト側の UID と合わなくて、コードを編集するのに都合が悪いため app コンテナでテスト以外のコード編集、ビルド、デプロイを行って glue コンテナでは、テストのみを行います。

### alias

app は、 dood (docker-outside-of-docker) で glue コンテナを操作できるようになっていて、そのための alias も作成されています。

```bash
glue                  # bash を起動
glue-spark-shell      # spark-shell を起動（Scala）
gluepyspark           # pyspark を実行（Python）
glue-spark-submit     # spark-submit を実行
gluepytest            # pytest を実行
```

### make

make コマンドの説明。

#### ローカル用コマンド

```bash
make install             # `poetry install` を実行
make lint                # linter (black, flake8) の実行
make build               # `poetry build` を実行
make test                # gluepytest を実行
make local-submit        # glue-spark-submit を実行
make fixture             # Faker でテストデータのCSVを作成
make send-awslocal       # localstack にテストデータを転送
```

#### AWS 環境に対して実行するコマンド

```bash
make send-aws            # AWS にテストデータを転送
make skeleton            # Glue ジョブのスケルトンを作成
make deploy              # Glue ジョブをデプロイする
make start-job-run       # Glue ジョブを実行する
```

## vscodeで使う場合

リモートコンテナで開発します。
VSCode をインストールして、リモートコンテナ拡張も入れてください。

### 初期設定

- リモートコンテナを開いたら、terminal を開いて以下を実行

    ```bash
    make install
    ```

- リモートコンテナを再起動する（Pylanceを再起動するため）

## pre-commit

pre-commit をインストールすると、ローカルでコミットする前に linter を強制実行することができて、コミットログをきれいに保つのに役立ちます。

```bash
pre-commit install
```
