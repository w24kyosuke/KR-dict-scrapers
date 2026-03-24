#!/bin/bash

echo "Proton VPNに接続しています..."
openvpn --config /app/vpn/[.ovpn設定ファイル名] \
        --auth-user-pass /app/vpn/pass.txt \
        --daemon \
        --log /app/vpn/openvpn.log \
        --pull-filter ignore "dhcp-option DNS"

echo "VPNの確立を待機中 (20秒)..."
sleep 20

echo "=== OpenVPN ログ (直近20行) ==="
tail -n 20 /app/vpn/openvpn.log
echo "==============================="

echo "現在のIPアドレスを確認します:"
curl -s https://api.ipify.org
echo ""

echo "スクレイピングを開始します..."
python3 [スクレイパーのコマンド]