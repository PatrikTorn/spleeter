# 🎵 Remove Drums from MP3 (Flask + Spleeter)

This simple Flask app allows users to upload an MP3 file and get a version with drums removed using [Spleeter](https://github.com/deezer/spleeter).

---

## 💡 Features

- Upload MP3 files via web UI
- Automatically removes drums
- Download the result as a WAV file

---


### Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

### Install dependencies
pip install -r requirements.txt

## Deploy
pkill -f app.py
nohup python3 app.py > flask.log 2>&1 &

## ⚙️ Setup on Amazon Linux EC2

### 1. Connect to EC2

```bash
ssh -i your-key.pem ec2-user@your-ec2-dns
