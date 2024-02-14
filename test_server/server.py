# -*- coding: utf-8 -*-

from flask import Flask, jsonify
from flask_cors import CORS

from log import logger
from code import ResponseCode, ResponseMessage

# 创建一个服务
app = Flask(__name__)
CORS(app, supports_credentials=True)


@app.route(rule='/api/test', methods=['GET'])
def test():
    result = "hello world!"
    success_response = dict(code=ResponseCode.SUCCESS, msg=ResponseMessage.SUCCESS, data=result)
    logger.info(success_response)
    return jsonify(success_response)


if __name__ == '__main__':
    # 解决中文乱码问题
    app.config['JSON_AS_ASCII'] = False
    # 启动服务，指定主机和端口
    app.run(host='0.0.0.0', port=1701, debug=False, threaded=True)