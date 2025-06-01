#!/bin/bash

# Exit on error
set -e

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root."
    exit 1
fi

echo "🔧 Installing rsyslog..."
apt update
apt install -y rsyslog

echo "🔧 Enabling TCP and UDP reception in rsyslog..."
RSYSLOG_CONF="/etc/rsyslog.conf"

# Uncomment relevant modules if commented
sed -i 's/^#module(load="imudp")/module(load="imudp")/' "$RSYSLOG_CONF"
sed -i 's/^#input(type="imudp" port="514")/input(type="imudp" port="514")/' "$RSYSLOG_CONF"
sed -i 's/^#module(load="imtcp")/module(load="imtcp")/' "$RSYSLOG_CONF"
sed -i 's/^#input(type="imtcp" port="514")/input(type="imtcp" port="514")/' "$RSYSLOG_CONF"

echo "📁 Creating log directory for remote hosts..."
mkdir -p /var/log/remote
chown syslog:adm /var/log/remote
chmod 750 /var/log/remote

echo "🛠️ Creating rsyslog rule for remote logging..."
cat <<EOF > /etc/rsyslog.d/10-remote.conf
# Remote logging template
template(name="RemoteLogs" type="string"
         string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log")

# Log all incoming messages from remote systems
*.* ?RemoteLogs
& stop
EOF

echo "🔄 Restarting rsyslog service..."
systemctl restart rsyslog
systemctl enable rsyslog

echo "✅ Rsyslog server setup complete."
