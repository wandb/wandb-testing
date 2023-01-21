set -e
ulimit -n 4096
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
export AWS_REGION=us-east-1
export S3_ENDPOINT=http://127.0.0.1:9000
export S3_USE_HTTPS=0
export S3_VERIFY_SSL=0
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin
export MINIO_HOST=127.0.0.1:9000

parent_dir=$(dirname "$0")

# if $parent_dir/bin does not exist, create it
if [ ! -d "$parent_dir"/s3tools/bin ]; then
    mkdir "$parent_dir"/s3tools/bin
fi

"$parent_dir"/s3tools/stop-s3.sh
sleep 1
"$parent_dir"/s3tools/start-s3.sh
sleep 1
"$parent_dir"/s3tools/setup-s3.sh
sleep 1

EXTRA=${*:-"tests/s3-beta/"}
time "$parent_dir"/regression.py --spec ::~broken $EXTRA
