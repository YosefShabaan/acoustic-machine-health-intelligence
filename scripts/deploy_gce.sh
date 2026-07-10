#!/bin/bash
# AMHI Fan MVP - GCE Deployment Script
#
# This script provisions a Google Compute Engine VM and configures it to run the AMHI Fan MVP
# using Docker Compose.

set -e

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# The user must set these variables or provide them via environment before running.

PROJECT_ID="${GCP_PROJECT_ID:-my-amhi-project}"
ZONE="${GCP_ZONE:-us-central1-a}"
INSTANCE_NAME="${GCP_INSTANCE_NAME:-amhi-fan-mvp}"
DOMAIN="${AMHI_DOMAIN:-localhost}"

# Provide standard values if not set
MACHINE_TYPE="e2-standard-2"
DISK_SIZE="30GB"

echo "================================================================================"
echo "Deploying AMHI Fan MVP to Google Compute Engine"
echo "Project: $PROJECT_ID"
echo "Zone:    $ZONE"
echo "VM Name: $INSTANCE_NAME"
echo "Domain:  $DOMAIN"
echo "================================================================================"

# ==============================================================================
# PROVISIONING
# ==============================================================================
# We use a Container-Optimized OS image, but since we need docker-compose, we
# will use a standard Debian/Ubuntu image and install Docker + Compose, or just
# use a startup script.

cat << 'EOF' > /tmp/startup.sh
#!/bin/bash
set -e

# 1. Install Docker and Docker Compose
apt-get update
apt-get install -y apt-transport-https ca-certificates curl software-properties-common git
curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 2. Setup directories
mkdir -p /opt/amhi/data/artifacts
mkdir -p /opt/amhi/runtime/uploads
cd /opt/amhi

# 3. User should upload ML artifacts to /opt/amhi/data/artifacts
# and provide docker-compose.prod.yml, Caddyfile, and .env file.
# Then run: docker compose -f docker-compose.prod.yml up -d
EOF

echo "Creating GCE Instance..."
gcloud compute instances create "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --boot-disk-size="$DISK_SIZE" \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --tags=http-server,https-server \
    --metadata-from-file startup-script=/tmp/startup.sh

echo "Creating firewall rules for HTTP/HTTPS..."
gcloud compute firewall-rules create allow-http-https \
    --project="$PROJECT_ID" \
    --allow tcp:80,tcp:443 \
    --target-tags=http-server,https-server || true

echo "================================================================================"
echo "VM Provisioned Successfully!"
echo "Next Steps:"
echo "1. SSH into the instance: gcloud compute ssh $INSTANCE_NAME --project=$PROJECT_ID --zone=$ZONE"
echo "2. Copy repository files, ML artifacts, and models to /opt/amhi"
echo "3. Create /opt/amhi/.env with your production secrets (GEMINI_API_KEY, AMHI_SESSION_SECRET, etc.)"
echo "4. Run: docker compose -f docker-compose.prod.yml up -d"
echo "================================================================================"
