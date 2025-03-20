import socket
import time

# 建立一个服务器端
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('192.168.125.230', 2000))  # 绑定要监听的端口
server.listen(5)  # 开始监听 表示可以使用五个链接排队
while True:  # conn 就是客户端链接过来而在服务器端为其生成的一个链接实例
    conn, addr = server.accept()  # 等待链接, 多个链接的时候就会出现问题, 其实返回了两个值
    print(conn, addr)
    print('主机与机器人通讯成功')

    d = 'trasfer_flask(7,17)'
    print(len(d))
    conn.send(d.encode('utf-8'))  # 发送数据

    data = conn.recv(1024)  # 接收数据
    print('receive:', data.decode())  # 打印接收到的数据
    conn.close()

