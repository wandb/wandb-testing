echo "Stopping minio..."
parent_dir=$(dirname "$0")
killall "$parent_dir"/bin/minio
echo "stopped."
