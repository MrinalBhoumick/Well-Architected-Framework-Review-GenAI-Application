#!/bin/bash
# Logs: /var/log/cloud-init-output.log

export AWS_DEFAULT_REGION=ap-south-1

max_attempts=5
attempt_num=1
success=false

# Retry loop for base installations
while [ "$success" = false ] && [ $attempt_num -le $max_attempts ]; do
  echo "Attempt $attempt_num: Installing packages..."

  sudo yum update -y
  sudo yum install -y python3 git docker iptables-services

  # Set default Python and pip
  sudo alternatives --install /usr/bin/python python /usr/bin/python3 1
  sudo alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

  # Remove conflicting requests package
  sudo yum remove -y python3-requests

  # Upgrade pip and install Python packages
  python3 -m pip install --upgrade pip
  python3 -m pip install boto3 awscli streamlit streamlit-lottie streamlit-authenticator numpy python-dotenv aws-cdk-lib constructs cdklabs.generative_ai_cdk_constructs

  if [ $? -eq 0 ]; then
    echo "Installation succeeded."
    success=true
  else
    echo "Attempt $attempt_num failed. Retrying in 10 seconds..."
    sleep 10
    attempt_num=$((attempt_num + 1))
  fi
done

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add ec2-user to docker group
sudo usermod -aG docker ec2-user

# Set up application directory
sudo mkdir -p /wafr-accelerator
sudo chown ec2-user:ec2-user /wafr-accelerator
cd /wafr-accelerator

# Clone the Streamlit app repo
sudo -u ec2-user git clone https://github.com/MrinalBhoumick/Well-Architected-Framework-Review-GenAI-Application.git

# Redirect port 80 to 8501 using iptables
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8501
sudo service iptables save
sudo systemctl enable iptables

# Create systemd service for Streamlit
sudo tee /etc/systemd/system/streamlit.service > /dev/null <<EOF
[Unit]
Description=Streamlit App
After=network.target docker.service

[Service]
ExecStart=/usr/local/bin/streamlit run /wafr-accelerator/Well-Architected-Framework-Review-GenAI-Application/app.py --server.port=8501 --server.enableCORS=false
WorkingDirectory=/wafr-accelerator/Well-Architected-Framework-Review-GenAI-Application
Restart=always
User=ec2-user
Environment=PATH=/usr/local/bin:/usr/bin
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the Streamlit service
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
