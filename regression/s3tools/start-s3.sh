set -e
if [ ! -f bin/minio ]; then
    curl https://dl.minio.io/server/minio/release/linux-amd64/minio -o bin/minio.tmp
    chmod +x bin/minio.tmp
    mv bin/minio.tmp bin/minio
fi

echo "Starting minio..."
nohup bin/minio server data/ >logs/minio.log 2>&1 &
echo "running"
