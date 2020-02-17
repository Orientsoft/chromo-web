# /usr/bin/python
# -*- coding:utf-8 -*-
import oss2
from io import BytesIO
import datetime
import uuid
import config

auth = oss2.Auth(config.ALI_ACCESS, config.ALI_SECRET)
endpoint = config.ALI_URL
dest_bucket = oss2.Bucket(auth, endpoint, config.ALI_DEST_BUCKET)
src_bucket = oss2.Bucket(auth, endpoint, config.ALI_SRC_BUCKET)


def Upload_Ali(file):
    try:
        st = file.stream.read()
        data = BytesIO(st)
        attr = file.filename.rsplit('.', 1)
        day = (datetime.datetime.now()).strftime('%Y-%m-%d')
        nonce = uuid.uuid1().hex
        # /日期/原文件名+uuid.jpg
        filename = '{}/{}@{}.jpg'.format(day, attr[0], nonce)
        result = src_bucket.put_object(filename, data)
        if result.status == 200:
            return filename
        else:
            print('图片上传失败')
            raise
    except Exception as e:
        return -1


def dest_url(filekey):
    url = dest_bucket.sign_url('GET', filekey, config.ALI_EXPIRE)
    return url


def src_url(filekey):
    url = src_bucket.sign_url('GET', filekey, config.ALI_EXPIRE)
    return url