set -e
echo "Setting up minio..."
parent_dir=$(dirname "$0")
"$parent_dir"/bin/mc alias set s3 http://127.0.0.1:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
set +e
"$parent_dir"/bin/mc mb s3/mybucket
set -e
echo "done."
