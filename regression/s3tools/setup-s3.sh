echo "Setting up minio..."
set -e
mkdir -p ~/.aws/
cp s3tools/aws-credentials.txt ~/.aws/credentials
cp s3tools/aws-config.txt ~/.aws/config
aws configure set default.s3.signature_version s3v4
set +e
aws --endpoint-url http://127.0.0.1:9000 s3 mb s3://mybucket
set -e
echo "done."
