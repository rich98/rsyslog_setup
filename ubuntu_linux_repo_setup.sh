!/bin/bash

REPO_NAME="myrepo"
REPO_DIR="/var/www/html/$REPO_NAME"
DEB_SOURCE_DIR="/mnt/debs"  # Your .deb package directory

# Ensure script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "Run as root."
   exit 1
fi

echo "Installing required packages..."
apt update
apt install -y apache2 dpkg-dev

echo "Creating repo directory..."
mkdir -p "$REPO_DIR"
cp "$DEB_SOURCE_DIR"/*.deb "$REPO_DIR"

echo "Generating Packages.gz..."
cd "$REPO_DIR"
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

echo "Enabling Apache..."
systemctl enable --now apache2

echo "Allowing HTTP through firewall..."
ufw allow 'Apache'

echo "Add this to your sources.list:"
echo "deb [trusted=yes] http://localhost/$REPO_NAME ./"
