#!/bin/bash
# Check output in /var/log/cloud-init-output.log
export AWS_DEFAULT_REGION={{REGION}}

max_attempts=5
attempt_num=1
success=false

# Adding retry loop for installation
while [ $success = false ] && [ $attempt_num -le $max_attempts ]; do
  echo "Trying to install required modules... (Attempt $attempt_num)"
  sudo yum update -y
  sudo yum install -y python3 git

  # Set python and pip aliases
  sudo alternatives --install /usr/bin/python python /usr/bin/python3 1
  sudo alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

  # Remove conflicting requests package
  yum remove -y python3-requests

  # Install required Python packages
  pip install --upgrade pip
  pip install boto3 awscli streamlit streamlit-authenticator numpy python-dotenv

  if [ $? -eq 0 ]; then
    echo "Installation succeeded!"
    success=true
  else
    echo "Attempt $attempt_num failed. Sleeping for 10 seconds and trying again..."
    sleep 10
    ((attempt_num++))
  fi
done

# Set up application directory
sudo mkdir -p /wafr-accelerator && cd /wafr-accelerator
sudo chown -R ec2-user:ec2-user /wafr-accelerator
chown -R ec2-user:ec2-user /wafr-accelerator

# Clone your application repo
cd /wafr-accelerator
git clone https://github.com/MrinalBhoumick/Well-Architected-Framework-Review-GenAI-Application.git
cd Well-Architected-Framework-Review-GenAI-Application

# Create a systemd service for Streamlit
sudo tee /etc/systemd/system/streamlit.service > /dev/null <<EOF
[Unit]
Description=Streamlit App
After=network.target

[Service]
ExecStart=/usr/bin/python -m streamlit run /wafr-accelerator/Well-Architected-Framework-Review-GenAI-Application/app.py --server.port=8501 --server.enableCORS=false
WorkingDirectory=/wafr-accelerator/Well-Architected-Framework-Review-GenAI-Application
Restart=always
User=ec2-user

[Install]
WantedBy=multi-user.target
EOF

# Start and enable the service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
