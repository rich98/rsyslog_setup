#!/bin/bash

# Variables
REPO_NAME="myrepo"
REPO_DIR="/var/www/html/$REPO_NAME"
REPO_CONF="/etc/yum.repos.d/$REPO_NAME.repo"
RPM_SOURCE_DIR="/path/to/your/rpms"  # <-- Change this to your actual RPM directory

# Ensure script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root." 
   exit 1
fi

echo "Creating repository directory at $REPO_DIR..."
mkdir -p "$REPO_DIR"

echo "Copying RPM packages..."
cp "$RPM_SOURCE_DIR"/*.rpm "$REPO_DIR"/

echo "Installing required packages..."
dnf install -y createrepo httpd

echo "Creating repository metadata..."
createrepo "$REPO_DIR"

echo "Creating repo configuration file at $REPO_CONF..."
cat > "$REPO_CONF" <<EOF
[$REPO_NAME]
name=My Custom Fedora Repo
baseurl=http://localhost/$REPO_NAME/
enabled=1
gpgcheck=0
EOF

echo "Configuring and starting Apache..."
systemctl enable --now httpd

echo "Adjusting firewall to allow HTTP traffic..."
firewall-cmd --add-service=http --permanent
firewall-cmd --reload

echo "Cleaning DNF cache and refreshing repo list..."
dnf clean all
dnf repolist

echo "Repository '$REPO_NAME' is ready and available at http://localhost