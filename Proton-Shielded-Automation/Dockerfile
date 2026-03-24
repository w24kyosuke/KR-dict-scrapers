# ベースイメージとしてUbuntu 22.04を使用
FROM ubuntu:22.04

# 対話的なプロンプトを無効化
ENV DEBIAN_FRONTEND=noninteractive

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    openvpn \
    curl \
    python3 \
    python3-pip \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# スクレイピング用のPythonライブラリをインストール
RUN pip3 install requests beautifulsoup4

# 作業ディレクトリを設定
WORKDIR /app

# ローカルのファイルをコンテナにコピー
COPY . /app

# 起動スクリプトに実行権限を付与
RUN chmod +x entrypoint.sh

# コンテナ起動時に実行されるスクリプトを指定
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]