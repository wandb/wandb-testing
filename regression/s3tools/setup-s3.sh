set -e
echo "Setting up minio..."
bin/mc alias set s3 http://127.0.0.1:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
set +e
bin/mc mb s3/mybucket
set -e
echo "done."
