import json
import os

from ftplib import FTP
import os
import sys
import time
import socket
from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)


class MyFTP:
    """
        ftp自动上传脚本
    """

    def __init__(self, host, port=21):
        """ 初始化 FTP 客户端
        参数:
                 host:ip地址

                 port:端口号
        """
        # print("__init__()---> host = %s ,port = %s" % (host, port))

        self.host = host
        self.port = port
        self.ftp = FTP()
        # 重新设置下编码方式
        self.ftp.encoding = 'gbk'
        self.log_file = open("log.txt", "a")
        self.file_list = []

    def login(self, username, password):
        """ 初始化 FTP 客户端
            参数:
                  username: 用户名

                 password: 密码
            """
        try:
            timeout = 60
            socket.setdefaulttimeout(timeout)
            # 0主动模式 1 #被动模式
            self.ftp.set_pasv(True)
            # 打开调试级别2，显示详细信息
            # self.ftp.set_debuglevel(2)

            self.debug_print('开始尝试连接到 %s' % self.host)
            self.ftp.connect(self.host, self.port)
            self.debug_print('成功连接到 %s' % self.host)

            self.debug_print('开始尝试登录到 %s' % self.host)
            self.ftp.login(username, password)

            self.debug_print('成功登录到 %s' % self.host)
            print("pwd:", self.ftp.welcome)
            self.debug_print(self.ftp.welcome)
        except Exception as err:
            self.deal_error("FTP 连接或登录失败 ，错误描述为：%s" % err)
            pass

    def is_same_size(self, local_file, remote_file):
        """判断远程文件和本地文件大小是否一致

           参数:
             local_file: 本地文件

             remote_file: 远程文件
        """
        try:
            remote_file_size = self.ftp.size(remote_file)
        except Exception as err:
            # self.debug_print("is_same_size() 错误描述为：%s" % err)
            remote_file_size = -1

        try:
            local_file_size = os.path.getsize(local_file)
        except Exception as err:
            # self.debug_print("is_same_size() 错误描述为：%s" % err)
            local_file_size = -1

        self.debug_print('local_file_size:%d  , remote_file_size:%d' % (local_file_size, remote_file_size))
        if remote_file_size == local_file_size:
            return 1
        else:
            return 0



    def upload_file(self, local_file, remote_file):
        """从本地上传文件到ftp

           参数:
             local_path: 本地文件

             remote_path: 远程文件
        """
        if not os.path.isfile(local_file):
            self.debug_print('%s 不存在' % local_file)
            return

        if self.is_same_size(local_file, remote_file):
            self.debug_print('跳过相等的文件: %s' % local_file)
            return

        buf_size = 1024
        file_handler = open(local_file, 'rb')

        self.ftp.storbinary('STOR %s' % remote_file, file_handler, buf_size)

        file_handler.close()
        print('上传: %s' % local_file + "成功!")
        self.debug_print('上传: %s' % local_file + "成功!")




    def close(self):
        """ 退出ftp
        """
        self.debug_print("close()---> FTP退出")
        self.ftp.quit()
        self.log_file.close()

    def debug_print(self, s):
        """ 打印日志
        """
        self.write_log(s)

    def deal_error(self, e):
        """ 处理错误异常
            参数：
                e：异常
        """
        log_str = '发生错误: %s' % e
        self.write_log(log_str)
        sys.exit()

    def write_log(self, log_str):
        """ 记录日志
            参数：
                log_str：日志
        """
        time_now = time.localtime()
        date_now = time.strftime('%Y-%m-%d %H:%M:%S', time_now)
        format_log_str = "%s ---> %s \n " % (date_now, log_str)
        self.log_file.write(format_log_str)


class FtpService(Resource):
    def get(self):
        my_ftp = MyFTP("172.16.105.4")
        my_ftp.login("zqhk", "ZQhk@1220")
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_names = os.listdir(BASE_DIR + "/data_files/")
        for filename in file_names:
            try:
                my_ftp.upload_file(BASE_DIR + "/data_files/"+filename, filename)
                if os.path.exists(BASE_DIR + "/data_files/"+filename):
                    os.remove(BASE_DIR + "/data_files/"+filename)
            except Exception as e:
                return {"code": 500, "msg": "服务器异常:" + e}
        return {"msg": "测试连接成功"}

    def post(self):
        data_type = request.headers.get('data_type')
        FILE_TYPE = ["checkIn", "checkOut", "hotelVisitor", "policeAppPlaceFiling"]
        if data_type in FILE_TYPE:
            filename = data_type + "_" + str(int(time.time() * 1000)) + ".json"
        else:
            return {"code": 400, "msg": "header-data_type error"}
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        data = request.get_data()
        loads = json.loads(data)
        json_str = json.dumps(loads,ensure_ascii=False)

        with open(BASE_DIR + "/data_files/" + filename, "w") as f:
            f.write(json_str)

   
        my_ftp = MyFTP("172.16.105.4")
        my_ftp.login("zqhk", "ZQhk@1220")
        file_names = os.listdir(BASE_DIR + "/data_files/")
        for filename in file_names:
            try:
                my_ftp.upload_file(BASE_DIR + "/data_files/"+filename, filename)
                if os.path.exists(BASE_DIR + "/data_files/"+filename):
                    os.remove(BASE_DIR + "/data_files/"+filename)
            except Exception as e:
                return {"code": 500, "msg": "服务器异常:" + e}


        return {"code": 200, "msg": "ok"}


api.add_resource(FtpService, '/ftpService')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=9563, threaded=True)
