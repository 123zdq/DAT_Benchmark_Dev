import select
import socket
import time
import av
import cv2
import os
import threading
import queue
from pynput import keyboard
from threading import Thread, Lock
from datetime import datetime
import sys

class DroneClient:
    def __init__(self, control_host='10.10.21.148', control_port=9999, 
                 video_port=7777, save_dir=None):
        # 控制部分参数
        self.control_host = control_host
        self.control_port = control_port
        self.socket_control = None
        self.active_keys = set()
        self.lock = Lock()
        self.control_running = False
        self.connect_success = False
        self.video_connected = False
        # 键盘映射配置
        self.key_mapping = {
            'w': (2, 0, 0, 0),
            's': (-2, 0, 0, 0),
            'a': (0, -1, 0, 0),
            'd': (0, 1, 0, 0),
            keyboard.Key.up: (0, 0, 2, 0),
            keyboard.Key.down: (0, 0, -2, 0),
            keyboard.Key.left: (0, 0, 0, -10),
            keyboard.Key.right: (0, 0, 0, 10),
            keyboard.Key.space: (0, 0, 0, 0)
        }
        
        # 视频部分参数
        self.video_port = video_port
        self.save_dir = save_dir
        self.video_writer = None
        self.frame_counter = 0
        self.last_save = time.time()
        self.start_time = time.time()
        self.last_fps_time = self.start_time
        self.fps_frame_count = 0
        self.total_frames = 0
        self.display_queue = queue.Queue(maxsize=1)
        self.video_running = False
        self.video_socket = None
        self.video_conn = None
        
        # 初始化视频解码器
        self._init_decoder()
        
        # 创建存储目录
        if self.save_dir:
            os.makedirs(self.save_dir, exist_ok=True)

        # ================ 新增：自动跟踪相关参数 ================
        self.current_action = 6  # 当前自动控制动作（默认停止）
        self.action_mapping = {  # action到控制向量的映射
            0: (3, 0, 0, 0),    # 0: 前进 → 对应'w'
            1: (-2, 0, 0, 0),   # 1: 后退 → 对应's'
            2: (0, -2, 0, 0),   # 2: 左移动 → 对应'a'
            3: (0, 2, 0, 0),    # 3: 右移动 → 对应'd'
            4: (0, -2, 0, -0),  # 4: 左转 → 对应左方向键
            5: (0, 2, 0, 0),   # 5: 右转 → 对应右方向键
            6: (0, 0, 0, 0)     # 6: 停止 → 对应space
        }
    
    # ================ 视频部分方法 ================
    def _init_decoder(self):
        """初始化解码器"""
        self.codec = av.CodecContext.create('h264', 'r')
        self.buffer = bytearray()
    
    def _save_frame(self, img):
        """保存单帧图像"""
        if self.save_dir and (time.time() - self.last_save) >= 0.03:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            path = os.path.join(self.save_dir, f"frame_{timestamp}.jpg")
            cv2.imwrite(path, img)
            self.last_save = time.time()
            print(f"保存截图: {path}")
    
    def _feed_data(self, data):
        """向解码器喂入数据"""
        try:
            packets = self.codec.parse(av.Packet(data))
            for packet in packets:
                frames = self.codec.decode(packet)
                
                for frame in frames:
                    if frame and frame.is_corrupt:
                        continue
                    if frame is not None:
                        img = frame.to_ndarray(format='bgr24')

                        # self._save_frame(img)
                        
                        # 更新帧率统计
                        self.fps_frame_count += 1
                        self.total_frames += 1
                        current_time = time.time()
                        elapsed = current_time - self.last_fps_time
                        
                        if elapsed >= 1.0:
                            real_fps = self.fps_frame_count / elapsed
                            total_elapsed = current_time - self.start_time
                            avg_fps = self.total_frames / total_elapsed
                            # print(f"帧率统计 - 实时: {real_fps:.2f} FPS, 平均: {avg_fps:.2f} FPS")
                            self.last_fps_time = current_time
                            self.fps_frame_count = 0
                        
                            # 处理队列逻辑
                        try:
                            # 尝试直接放入队列
                            self.display_queue.put_nowait(img)
                        except queue.Full:
                            # 队列已满时，先移除旧帧再添加新帧
                            try:
                                self.display_queue.get_nowait()  # 移除旧帧
                                self.display_queue.put_nowait(img)  # 添加新帧
                            except queue.Empty:
                                # 若队列为空（理论上不会出现），直接添加
                                self.display_queue.put_nowait(img)
        except av.AVError as e:
            print(f"解码错误: {e}")
            self._reset_decoder()
    
    def _reset_decoder(self):
        """重置解码器"""
        print("重置解码器...")
        self.codec = None
        self._init_decoder()
        self.buffer.clear()
    
    def process_packet(self, data):
        """处理网络数据包"""
        self.buffer += data
        
        while True:
            start_code = b'\x00\x00\x00\x01'
            start_idx = self.buffer.find(start_code)
            
            if start_idx == -1:
                break
            
            if start_idx > 0:
                del self.buffer[:start_idx]
            
            end_idx = self.buffer.find(start_code, 4)
            if end_idx == -1:
                break
            
            nal_unit = bytes(self.buffer[:end_idx])
            del self.buffer[:end_idx]
            self._feed_data(nal_unit)
    
    def _video_display_thread(self):
        """视频显示线程"""
        cv2.namedWindow('Drone Video', cv2.WINDOW_NORMAL)
        while self.video_running:
            try:
                img = self.display_queue.get(timeout=0.1)
                # self._save_frame(img)
                cv2.imshow('Drone Video', img)
                key = cv2.waitKey(33) & 0xFF
                if key == 27:  # ESC退出
                    self.stop()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"显示错误: {e}")
        
        cv2.destroyAllWindows()
    
    def _video_server_thread(self):
        """视频服务器线程"""
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.video_socket.bind(('0.0.0.0', self.video_port))
        self.video_socket.listen(1)
        print(f"视频服务器已启动，端口: {self.video_port}")

        # 新增：视频连接状态标志
        self.video_connected = False
        
        try:
            while self.video_running:
                try:
                    self.video_conn, addr = self.video_socket.accept()
                    print(f"视频客户端已连接: {addr}")
                    self.connect_success = True
                    self.video_connected = True  # 连接成功，设置标志为True
                    self.video_conn.settimeout(1.0)
                    
                    while self.video_running:
                        try:
                            data = self.video_conn.recv(65535)
                            if not data:
                                print("视频连接断开")
                                break
                            self.process_packet(data)
                        except socket.timeout:
                            continue
                        except Exception as e:
                            print(f"视频接收错误: {e}")
                            break
                except Exception as e:
                    print(f"视频服务器错误: {e}")
                finally:
                    if self.video_conn:
                        self.video_conn.close()
                        self.video_conn = None
                    print("等待新视频连接...")
        finally:
            self.video_socket.close()
    
    # ================ 控制部分方法 ================
    def _connect_control(self):
        """建立控制连接"""
        try:
            self.socket_control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_control.connect((self.control_host, self.control_port))
            print(f"控制连接成功: {self.control_host}:{self.control_port}")
            return True
        except Exception as e:
            print(f"控制连接失败: {e}")
            return False
    
    def on_press(self, key):
        """处理按键按下事件"""
        with self.lock:
            if key in self.key_mapping or getattr(key, 'char', None) in self.key_mapping:
                self.active_keys.add(key)
    
    def on_release(self, key):
        """处理按键释放事件"""
        if key == keyboard.Key.esc or getattr(key, 'char', None) == 'q':
            self.stop()
            return False
            
        with self.lock:
            if key in self.active_keys:
                self.active_keys.remove(key)
    
    def _keyboard_listener_thread(self):
        """键盘监听线程"""
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            listener.join()
    
    def _control_send_thread(self):
        """控制指令发送线程"""
        while self.control_running:
            try:
                with self.lock:
                    current_keys = list(self.active_keys)
                
                command_vector = [0, 0, 0, 0]
                for key in current_keys:
                    mapping_key = key if key in self.key_mapping else getattr(key, 'char', None)
                    if mapping_key in self.key_mapping:
                        for i, value in enumerate(self.key_mapping[mapping_key]):
                            command_vector[i] += value
                    
                    command_vector = [max(-100, min(100, v)) for v in command_vector]
                    message = f"{command_vector[0]},{command_vector[1]},{command_vector[2]},{command_vector[3]}\n"
                    self.socket_control.sendall(message.encode())
                
                # time.sleep(0.05)
            except Exception as e:
                print(f"控制发送错误: {e}")
                self.stop()
                break

    # ================ 新增：视觉跟踪相关方法 ================
    def get_vision_input(self):
        """
        从display_queue获取最近的图像并处理为84x84尺寸
        返回: 84x84x3的BGR图像（ndarray），若获取失败则返回None
        """
        try:
            img = self.display_queue.get(timeout=0.1)

            # cv2.imshow('Drone Original Video ', img)
            # cv2.waitKey(1) & 0xFF
            
            # 检查原始图像尺寸是否符合预期（1440x1080）
            if img.shape[0] != 1080 or img.shape[1] != 1440:
                print(f"警告：原始图像尺寸不符（预期1920x1080，实际{img.shape[1]}x{img.shape[0]}）")
                # 仍尝试按比例裁剪，避免程序中断
                target_size = min(img.shape[0], img.shape[1])
                crop_width = target_size
                crop_height = target_size
            else:
                # 原始尺寸为1920x1080，裁剪为1080x1080
                crop_width = 1080
                crop_height = 1080
            
            # # 计算裁剪区域（从中心裁剪）
            # center_x = img.shape[1] // 2
            # center_y = img.shape[0] // 2
            # half_width = crop_width // 2
            # half_height = crop_height // 2
            
            # # 裁剪区域坐标（确保不越界）
            # start_x = max(0, center_x - half_width)
            # end_x = min(img.shape[1], center_x + half_width)
            # start_y = max(0, center_y - half_height)
            # end_y = min(img.shape[0], center_y + half_height)
            
            # # 执行裁剪
            # cropped_img = img[start_y:end_y, start_x:end_x]

            # 目标裁剪尺寸
            target_size = 840

            # 计算裁剪区域（从中心裁剪）
            center_x = img.shape[1] // 2
            center_y = img.shape[0] // 2
            half_size = target_size // 2

            # 裁剪区域坐标（确保不越界）
            start_x = max(0, center_x - half_size)
            end_x = min(img.shape[1], center_x + half_size)
            start_y = max(0, center_y - half_size)
            end_y = min(img.shape[0], center_y + half_size)

            # 执行裁剪
            cropped_img = img[start_y:end_y, start_x:end_x]
            # print(f"裁剪后尺寸: {cropped_img.shape[1]}x{cropped_img.shape[0]}")  # 调试信息，可删除
            
            # 调整裁剪后的图像尺寸为84x84
            resized_img = cv2.resize(cropped_img, (84, 84), interpolation=cv2.INTER_AREA)
            
            return cropped_img, resized_img
        except queue.Empty:
            print("警告：display_queue为空，无法获取图像")
            return None, None
        except Exception as e:
            print(f"获取视觉输入失败: {e}")
            return None, None

    
    def send_action_command(self, action):
        """
        发送基于action的控制指令
        参数: action - 0-6的整数（对应前进、后退、左移、右移、左转、右转、停止）
        返回: 发送成功则返回True，否则返回False
        """
        # 定义动作编号到名称的映射
        ACTION_NAMES = {
            0: "前进",
            1: "后退",
            2: "左移",
            3: "右移",
            4: "左转",
            5: "右转",
            6: "停止"
        }
        # 校验action有效性
        if not isinstance(action, int) or not (0 <= action <= 6):
            print(f"无效action: {action}，必须是0-6的整数")
            return False
        
        # 校验控制连接
        if not self.socket_control:
            print("控制连接未建立，无法发送指令")
            return False
        
        try:
            # 获取action对应的控制向量
            command_vector = self.action_mapping.get(action, (0, 0, 0, 0))
            # 限制指令范围
            command_vector = [max(-100, min(100, v)) for v in command_vector]
            # 格式化并发送指令
            message = f"{command_vector[0]},{command_vector[1]},{command_vector[2]},{command_vector[3]}\n"
            self.socket_control.sendall(message.encode())
            # 使用映射名称替代数字编号
            action_name = ACTION_NAMES.get(action, f"未知动作({action})")
            # print(f"发送action指令: {action_name} → {message.strip()}")
            return True
        except Exception as e:
            print(f"发送action指令失败: {e}")
            return False
    
    # ================ 公共方法 ================
    def start(self):
        """启动无人机客户端"""
        # 启动控制部分
        if not self._connect_control():
            return
        
        self.control_running = True
        # Thread(target=self._keyboard_listener_thread, daemon=True).start()
        # Thread(target=self._control_send_thread, daemon=True).start()
        
        # 启动视频部分
        self.video_running = True
        # Thread(target=self._video_display_thread, daemon=True).start()
        Thread(target=self._video_server_thread, daemon=True).start()
        
        print("无人机客户端已启动")
        print("使用WASD和方向键控制无人机，ESC或Q退出")
    
    def stop(self):
        """停止无人机客户端"""
        print("正在停止无人机客户端...")
        self.control_running = False
        self.video_running = False
        
        # 关闭控制套接字
        if self.socket_control:
            self.socket_control.close()
            self.socket_control = None
        
        # 关闭视频套接字
        if self.video_conn:
            self.video_conn.close()
            self.video_conn = None
        if self.video_socket:
            self.video_socket.close()
            self.video_socket = None
        
        print("无人机客户端已停止")


if __name__ == "__main__":
    # 使用示例
    drone = DroneClient(
        control_host='10.10.21.148', 
        control_port=9999,
        video_port=7777,
        save_dir='/home/cunning/视频/img/'  # 替换为实际保存路径
    )

    # 动作含义映射表（用于控制台提示）
    action_descriptions = {
        0: "前进",
        1: "后退",
        2: "左移动",
        3: "右移动",
        4: "左转",
        5: "右转",
        6: "停止"
    }
    
    try:
        # 启动无人机客户端
        drone.start()
        print("\n===== 动作控制测试程序 =====")
        print("动作指令对应表：")
        for action, desc in action_descriptions.items():
            print(f"  {action} - {desc}")
        print("输入 'q' 或 'Q' 退出程序")
        print("==========================\n")

        # 主线程保持运行
        while drone.control_running or drone.video_running:
            # 获取并显示图像（可选）
            img = drone.get_vision_input()
            if img is not None:
                cv2.imshow('Drone Video', img)
                # 检测ESC键退出（图像窗口按键）
                key = cv2.waitKey(10) & 0xFF
                if key == 27:  # ESC键
                    drone.stop()
                    break
            
            # 处理控制台键盘输入（非阻塞）
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                input_str = sys.stdin.readline().strip()
                if input_str.lower() == 'q':  # 退出指令
                    drone.stop()
                    break
                elif input_str.isdigit():  # 动作指令
                    action = int(input_str)
                    if 0 <= action <= 6:
                        # 发送动作指令
                        success = drone.send_action_command(action)
                        if success:
                            print(f"已发送动作：{action} - {action_descriptions[action]}")
                        else:
                            print(f"发送动作 {action} 失败")
                    else:
                        print("无效动作！请输入 0-6 之间的数字")
                else:
                    print("输入无效！请输入 0-6 之间的数字，或输入 'q' 退出")
    except KeyboardInterrupt:
        drone.stop()
    finally:
        cv2.destroyAllWindows()
        print("程序已退出")