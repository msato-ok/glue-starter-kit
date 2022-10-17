# glue-starter-kit

AWS Glue ジョブをローカルで開発するスターターキット

## Docker コンテナの構成

- app  
    このコンテナは VSCode 用のリモートコンテナで、テスト以外のコード編集や linting を行うことを目的としています。
- glue  
    AWS 製の Glue コンテナです。
    テストを行うためのコンテナです。
- localstack  
    S3 のエミュレータ。

glue コンテナの UID が 10000 になっていて、ホスト側の UID と合わなくて、コードを編集するのに都合が悪いため app コンテナでテスト以外のコード編集、ビルド、デプロイを行って glue コンテナでは、テストのみを行います。

### alias

app コンテナ内から glue コンテナのコマンドを実行するための alias が作成されています。

    glue                  # bash を起動
    glue-spark-shell      # spark-shell を起動（Scala）
    gluepyspark           # pyspark を実行（Python）
    glue-spark-submit     # spark-submit を実行
    gluepytest            # pytest を実行

### make

make コマンドの説明。

    make install             # `poetry install` を実行
    make lint                # linter (black, flake8) の実行
    make test                # gluepytest を実行
    make build               # `poetry build` を実行
    make submit              # glue-spark-submit を実行
