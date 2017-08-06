# GCP_Remover

## Installations
- Google Cloud Platform SDK - `gcloud` and `gsutil`
- Python3

---

## Requirements
- Make sure you have already logged in a Google Cloud Platform project.
- Please make sure that when you insert the argument `expiration`, it is the ISO-format. Be aware of that it is supposed to be UTC time.

---

## Usage

```bash
$ ./remover.py -h

usage: remover.py [-h] [-t T] bucket expiration

a script to delete old videos

positional arguments:
  bucket      bucket to delete
  expiration  ISO format <YYYY-mm-ddTHH:MM:SSZ>

optional arguments:
  -h, --help  show this help message and exit
  -t T        thread count
```