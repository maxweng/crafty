import json
import boto3
from chalice import Chalice, Response
from random import randint

S3 = boto3.client('s3', region_name='us-east-2')
BUCKET = 'zeppelin-solutions-dev'
DIR = 'crafty'

app = Chalice(app_name='crafty-backend')

# Generic decorator to catch misc errors
def error_catching(func):
  def wrapper():
    try:
      return func()
    except Exception as e:
      return error_response(str(e))
  return wrapper

# Decorator to limit the payload of a request's body
def limit_raw_body_kb(max_kbytes):
  def limit_raw_body_kb_fixed(func):
    def wrapper():
      if len(app.current_request.raw_body) > (max_kbytes * 1024):
        return error_response('max data size is %skB' % max_kbytes)
      else:
        return func()
    return wrapper
  return limit_raw_body_kb_fixed

def ok_response(msg):
  return Response(body=msg,
           status_code=200,
           headers={'Content-Type': 'text/plain'})

def error_response(msg):
  return Response(body='Error: %s' % msg,
           status_code=500,
           headers={'Content-Type': 'text/plain'})

# Metadata

@app.route('/%s/metadata' % DIR , methods=['POST'], cors=True)
@error_catching
@limit_raw_body_kb(2)
def upload_metadata():
  key = get_metadata_key(randint(0, 2 ** 32))
  S3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(app.current_request.json_body), ACL='public-read')
  return ok_response('https://s3.amazonaws.com/%s/%s' % (BUCKET, key))

def get_metadata_key(uuid):
  return '%s/metadata/%s.json' % (DIR, uuid)

# Thumbnail

@app.route('/%s/thumbnail' % DIR , methods=['POST'], cors=True)
@error_catching
@limit_raw_body_kb(1000)
def upload_thumbnail():
  uuid = randint(0, 2 ** 32)

  tmp_file_name = '/tmp/%s' % uuid
  with open(tmp_file_name, 'wb') as tmp_file:
    tmp_file.write(app.current_request.json_body['image-base64'].decode('base64'))

  key = get_thumbnail_key(uuid)
  S3.upload_file(Filename=tmp_file_name, Bucket=BUCKET, Key=key, ExtraArgs={'ACL': 'public-read'})

  return ok_response('https://s3.amazonaws.com/%s/%s' % (BUCKET, key))

def get_thumbnail_key(uuid):
  return '%s/thumbnail/%s' % (DIR, uuid)
