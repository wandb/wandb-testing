set -e
parent_dir=$(dirname "$0")
if [ ! -f "$parent_dir"/bin/minio ]; then
    curl https://dl.minio.io/server/minio/release/linux-amd64/minio -o "$parent_dir"/bin/minio.tmp
#    curl https://dl.minio.io/server/minio/release/darwin-arm64/minio -o "$parent_dir"/bin/minio.tmp
    chmod +x "$parent_dir"/bin/minio.tmp
    mv "$parent_dir"/bin/minio.tmp "$parent_dir"/bin/minio
fi
if [ ! -f "$parent_dir"/bin/mc ]; then
    curl https://dl.minio.io/client/mc/release/linux-amd64/mc -o "$parent_dir"/bin/mc.tmp
#    curl https://dl.minio.io/client/mc/release/darwin-arm64/mc -o "$parent_dir"/bin/mc.tmp
    chmod +x "$parent_dir"/bin/mc.tmp
    mv "$parent_dir"/bin/mc.tmp "$parent_dir"/bin/mc
fi

echo "Starting minio..."
nohup "$parent_dir"/bin/minio server "$parent_dir"/../data/ >"$parent_dir"/../logs/minio.log 2>&1 &
echo "running"
