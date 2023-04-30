set -e
parent_dir=$(dirname "$0")
if [ ! -f bin/minio ]; then
    curl https://dl.minio.io/server/minio/release/linux-amd64/minio -o bin/minio.tmp
#    curl https://dl.minio.io/server/minio/release/darwin-arm64/minio -o bin/minio.tmp
    chmod +x bin/minio.tmp
    mv bin/minio.tmp bin/minio
fi
if [ ! -f bin/mc ]; then
    curl https://dl.minio.io/client/mc/release/linux-amd64/mc -o bin/mc.tmp
#    curl https://dl.minio.io/client/mc/release/darwin-arm64/mc -o bin/mc.tmp
    chmod +x bin/mc.tmp
    mv bin/mc.tmp bin/mc
fi

echo "Starting minio..."
nohup bin/minio server data/ >logs/minio.log 2>&1 &
echo "running"
